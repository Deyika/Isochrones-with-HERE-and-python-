import numpy as np 
import cartopy.crs as ccrs
import flexpolyline as fp
from matplotlib import cm 
from matplotlib.path import Path
from matplotlib.patches import PathPatch



def here_geocode_request(search,apiKey, limit=1):
    ''' Create a Here geocoding API request for a given search string. 
    search: search string.
    apiKey: your private Here API key
    limit: max number of search results returned from the API'''
    
    url = 'https://discover.search.hereapi.com/v1/geocode?apiKey'
    url+=apiKey
    url+='&limit='+str(limit)
    url+='&q='+search.replace(' ','+')
    
    return url


def here_isoline_request(origin_point, transport_mode, range_values, range_type, apiKey, departure_time = False, reverse=False):
    '''
    Create a Here isoline API request for a given lat-lon coords, transport type, departure time and ranges.
    origin_point: [Lat, Lon]
    transportMode: 'car' etc. (See here documentation for full list)
    range_values: float or list of ranges for isolines
    range_type: 'time' or 'distance'
    apiKey: your private Here API key
    departure_time: departure time for traffic calculation. If False, traffic ignored.
    reverse: if true, the origin point will be treated as a destination.
    '''
    
    url = "https://isoline.router.hereapi.com/v8/isolines?"
    origin='origin'
    depature='departureTime'
    if reverse:
        origin='destination'
        depature = 'arrivalTime'
        
    url = (url+
               'apiKey'+apiKey+
               '&transportMode='+transport_mode+
               '&'+origin+'='+str(origin_point[0])+','+str(origin_point[1])+
               '&range[type]='+range_type+
               '&range[values]=')
    
    values = ''
    try:
        for r in range_values:
            values+=str(r)+','
    except:
        values+=str(range_values)+','
        
    url += values[:-1]
    
    if departure_time!=False:
        url += '&'+depature+'='+departure_time
    
    return url

def here_isolines_to_WGS84(here_response):
    '''
    Converts compressed flexible polygon response from the Here isoline API to lat-lon coords.
    '''
    
    isolines={}
    for iso in here_response['isolines']:
        coords = np.array(list(p for p in fp.iter_decode(iso['polygons'][0]['outer'])))
        value = iso['range']['value']
        isolines[value]=coords
    
    return isolines

def find_extent(all_poly, buffer=0.1):
    '''
    Creates a extent around a given set of polygons with a buffer.
    all_poly: list of np.arrays with columns containing longitude and latitude coords.
    buffer: ratio of blank space to allow on border of map, as a ratio of the length of the polygon in lat/lon
    '''
    
    lon_max = -np.inf
    lon_min = np.inf
    lat_max = -np.inf 
    lat_min = np.inf 
    
    for Poly in all_poly:
        if np.max(Poly[:,0])>lon_max:
            lon_max=np.max(Poly[:,0])
        if np.min(Poly[:,0])<lon_min:
            lon_min = np.min(Poly[:,0])
        if np.max(Poly[:,1])>lat_max:
            lat_max = np.max(Poly[:,1])
        if np.min(Poly[:,1])<lat_min:
            lat_min=np.min(Poly[:,1])
                
    lon_buffer = abs(lon_max-lon_min)*buffer
    lat_buffer = abs(lon_max-lon_min)*buffer
    
    top = lon_max+lon_buffer
    bottom = lon_min-lon_buffer
    left = lat_min-lat_buffer
    right = lat_max+lat_buffer
    
    return [ bottom, top, left, right]

def plot_isolines(isolines, ax, cmap=cm.get_cmap('viridis'), units='seconds', ax_units='minutes', label_rounding = 1, contour_lines=0, alpha=0.3):
    
    ''' 
    Plots isolines from HERE API onto matplotlib GeoAxes. Ensures that the larger isolines are not overlapping the smaller ones for plotting clarity.
    isolines: a dict in the form of {range: polygon coords (lat/lon)}
    ax: matplotlib GeoAxesSubplot
    cmap: matplotlib colormap
    units: isoline native range units (string)
    ax_units: output unit for isoline labelling (string)
    label_rounding: number of decimal places to round isoline labels (int)
    contour_lines: linewidth of contour lines. Set to 0 for no lines.
    alpha: opacity of the plotted polygons.
    
    '''
    
    
    # get isoline ranges 
    ranges = list(isolines.keys())
    
    # Get polygons into list with lon/lat format
    polygons = [np.hstack((np.vstack(isolines[value][:,1]), np.vstack(isolines[value][:,0]))) for value in ranges]
    
    get_c = lambda i, n: 1-(1/(n))*i-(1/(2*n))
    
    # Check for formatting correctness.
    if units not in ['s','seconds','min','minutes','hours','h','m','meters','km','kilometers','kms','ft','feet','foot','yard','yrd','yards','mile','miles', 'mi', 'mls']:
        print("Incorrect isoline unit specification, please ensure it is one of: 's','seconds','min','minutes','hours','h','m','meters','km','kilometers','kms','ft','feet','foot','yard','yrd','yards','mile','miles', 'mi', 'mls'")
        return None
    if ax_units not in ['s','seconds','min','minutes','hours','h','m','meters','km','kilometers','kms','ft','feet','foot','yard','yrd','yards','mile','miles', 'mi', 'mls']:
        print("Incorrect axis unit specification, please ensure it is one of: 's','seconds','min','minutes','hours','h','m','meters','km','kilometers','kms','ft','feet','foot','yard','yrd','yards','mile','miles', 'mi', 'mls'")
        return None
    if (units in ['s','seconds','min','minutes','hours','h']) and (ax_units in ['m','meters','km','kilometers','kms','ft','feet','foot','yard','yrd','yards','mile','miles', 'mi', 'mls']):
        print('Incompatible isoline and axis units (time and distance respectively).')
        return None
    if (units not in ['s','seconds','min','minutes','hours','h']) and (ax_units not in ['m','meters','km','kilometers','kms','ft','feet','foot','yard','yrd','yards','mile','miles', 'mi', 'mls']):
        print('Incompatible isoline and axis units (distance and time respectively).')
        return None
    
    # Convert units
    if units.lower() in ['s','seconds']:
        values = np.array(ranges)
    elif units.lower() in ['min','minutes']:
        values = np.array(ranges)*60
    elif units.lower() in ['hours','h']:
        values = np.array(ranges)*60*60
    elif units.lower() in ['m', 'meters']:
        values = np.array(ranges)
    elif units.lower() in ['km', 'kilometers','kms']:
        values = np.array(ranges)*1000
    elif units.lower() in ['ft','feet','foot']:
        values = np.array(ranges)*0.3048
    elif units.lower() in ['yard','yrd','yards']:
        values = np.array(ranges)*0.9144
    elif units.lower() in ['mile','miles', 'mi', 'mls']:
        values = np.array(ranges)*1609.344

    if ax_units.lower() in ['s','seconds']:
        values = values
    elif ax_units.lower() in ['min','minutes']:
        values = values/60
    elif ax_units.lower() in ['hours','h']:
        values = values/(60*60)
    elif ax_units.lower() in ['m', 'meters']:
        values = values
    elif ax_units.lower() in ['km', 'kilometers','kms']:
        values = values/1000
    elif ax_units.lower() in ['ft','feet','foot']:
        values = values/0.3048
    elif ax_units.lower() in ['yard','yrd','yards']:
        values = values/0.9144
    elif ax_units.lower() in ['mile','miles', 'mi', 'mls']:
        values = values/1609.344
        
    # Plot isolines
    for i in range(len(polygons)):
        if i == 0:
            
            poly_C = [Path.LINETO for p in polygons[i]]
            poly_C[0] = Path.MOVETO
            codes = []
            
            codes.extend(poly_C)
            ax.add_patch(PathPatch(Path(polygons[i],codes),
                                          lw=contour_lines,
                                          facecolor=cmap(get_c(i,len(ranges))), 
                                          transform=ccrs.Geodetic(),
                                          alpha=alpha,
                                          label=str(round(0.0,label_rounding))+'-'+str(round(values[i],label_rounding))+' '+ax_units))
        else:
            path = patch_between(polygons[i], polygons[i-1])
            ax.add_patch(PathPatch(path, 
                                   facecolor=cmap(get_c(i,len(ranges))), 
                                   lw=contour_lines,
                                   transform=ccrs.Geodetic(),
                                   alpha=alpha,
                                   label=str(round(values[i-1],label_rounding))+'-'+str(round(values[i],label_rounding))+' '+ax_units))
        
            
def scale_bar(ax, length=None, location=(0.5, 0.05), linewidth=3):
    """
    ax: matplotlib GeoAxesSubplot
    length: length of the scalebar in km.
    location: center of the scalebar in axis coordinates. (ie. 0.5 is the middle of the plot)
    linewidth: thickness of the scalebar.
    """
    #Get the limits of the axis in lat long
    llx0, llx1, lly0, lly1 = ax.get_extent(ccrs.PlateCarree())
    #Make tmc horizontally centred on the middle of the map,
    #vertically at scale bar location
    sbllx = (llx1 + llx0) / 2
    sblly = lly0 + (lly1 - lly0) * location[1]
    tmc = ccrs.TransverseMercator(sbllx, sblly)
    #Get the extent of the plotted area in coordinates in metres
    x0, x1, y0, y1 = ax.get_extent(tmc)
    #Turn the specified scalebar location into coordinates in metres
    sbx = x0 + (x1 - x0) * location[0]
    sby = y0 + (y1 - y0) * location[1]

    #Calculate a scale bar length if none has been given
    #(Theres probably a more pythonic way of rounding the number but this works)
    if not length: 
        length = (x1 - x0) / 5000 #in km
        ndim = int(np.floor(np.log10(length))) #number of digits in number
        length = round(length, -ndim) #round to 1sf
        #Returns numbers starting with the list
        def scale_number(x):
            if str(x)[0] in ['1', '2', '5']: return int(x)        
            else: return scale_number(x - 10 ** ndim)
        length = scale_number(length) 

    #Generate the x coordinate for the ends of the scalebar
    bar_xs = [sbx - length * 500, sbx + length * 500]
    #Plot the scalebar
    ax.plot(bar_xs, [sby, sby], transform=tmc, color='k', linewidth=linewidth)
    #Plot the scalebar label
    ax.text(sbx, sby, str(length) + ' km', transform=tmc,
            horizontalalignment='center', verticalalignment='bottom')
    
def patch_between(poly1, poly2):
    ''' 
    Returns a path with a hollow section defined as the intersection of poly1 and poly2
    poly1/poly2: numpy array with columns countain longitude and latitude coords. 
    '''
    
    poly1_C = [Path.LINETO for p in poly1]
    poly1_C[0] = Path.MOVETO
    
    poly2_C = [Path.LINETO for p in poly2]
    poly2_C[0] = Path.MOVETO
    
    vertices = []
    vertices.extend(poly1)
    vertices.extend(poly2[::-1])
    
    codes = []
    codes.extend(poly1_C)
    codes.extend(poly2_C)
    
    return Path(vertices, codes)

