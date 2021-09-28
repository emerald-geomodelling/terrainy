# terrainy
Contains tools to get user defined resolution DTM's covering available countries

Example:

`import terrainy`\
`from terrainy import  getDTM, countries`

`print(countries)`

`output: {'Norway': ['https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm-nhm-25833?service=wcs&request=getcapabilities',
  '1.0.0',
  'dtm_25833',
  'EPSG:25833']}`

With the example of Norway's 1m DTM

`getDTM("Norway", "/User/defined/shapefile/inEPSG25833.shp', 1, /Out/path/DTM.tif)`

