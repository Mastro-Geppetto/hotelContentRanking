import pandas as pd
import numpy as np

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

import plotly.graph_objects as go

###################
## Utils
###################
def is_attr_invalid( value ):
  if type(value) is bool:
    return not value
  if 'False' in value or 'NONE' in value:
    return True
  return False

def is_hotel_attr( attr ):
  return attr in ['HotelCode',
                  'HotelName',
                  'SegmentCategory',
                  'Services',
                  'AcceptedPayments',
                  'CheckInTime',
                  'CheckOutTime',
                  'RefPoint',
                  'Phone',
                  'PolicyInfo',
                  'PenaltyDescription',
                  'TaxPolicies',
                  'CommissionPolicy',
                  'Dinning',
                  'MeetingRooms',
                  'LanguageSpoken']

##########################################
## pandas datastore, will cache everything
##########################################
class dataStore( object ):
  def __init__( self,
                pickle_file_path = './dataDump.zip',
                chain_url_base_str = '/chain?ChainCode=',
                hotel_url_base_str = '/hotel?HotelCode=',
                # hard coded
                chain_2_name_map   = {
                  'BY' : 'Banyan Tree'      ,
                  'CP' : 'Crowne Plaza'     ,
                  'DT' : 'DoubleTree'       ,
                  'FN' : 'Fairfield Inn'    ,
                  'FR' : 'RocketFuel'       ,
                  'HL' : 'Hilton'           ,
                  'HI' : 'Holiday Inn'      ,
                  'IC' : 'Intercontinental' ,
                  'LR' : 'The Leela Palace' ,
                  'LW' : 'The Leading Hotels of the World',
                  'MC' : 'Marriott'         ,
                  'MK' : 'Movenpick'        ,
                  'MN' : 'Montage'          ,
                  'MV' : 'MGM'              ,
                  'NH' : 'NH Hotel group'     ,
                  'ON' : 'One and Only Hotels',
                  'PI' : 'Premier Inn'      ,
                  'PK' : 'Park Plaza'       ,
                  'PU' : 'Pullman'          ,
                  'RD' : 'Radisson Blu'     ,
                  'RX' : 'Rixos'            ,
                  'RT' : 'Accor'            ,
                  'SB' : 'Sofitel'          ,
                  'SH' : 'Scandic'          ,
                  'SI' : 'Sheraton'         ,
                },
              ):
    # save a copy
    self.chain_2_name_map = chain_2_name_map.copy()
    self.name_2_chain_map = { v : k for k,v in self.chain_2_name_map.items() }
    
    ##################################
    # read preprocessed pickle file
    df = pd.read_pickle( pickle_file_path )
    self.attributes = list( df.columns[:-1] ) # except score
    # drop test hotels
    df = df[ df.HotelName.str.contains('TEST', case=False) == False ]
    
    # sort based on 'HotelCode'
    df = df.set_index('HotelCode').sort_index().reset_index( 'HotelCode' )
    
    # update score of hotels
    df = df.assign( Score = df.Score * 100)
    df = df.assign( Score = df.Score.astype(int) )
    
    # drop duplicate rows with same hotel name & retain row with higher score
    if not df.HotelName.is_unique:
      df = df.drop_duplicates( subset='HotelName', keep='last' )
    
    self.total_hotels = len(df)
    
    # add chain code & chain name to table
    df = df.assign( ChainCode = df['HotelCode'].str[0:2] )
    df = df.assign( ChainName = df['ChainCode'] )
    df['ChainName'] = df['ChainName'].replace( self.chain_2_name_map )
    
    # add chain & hotel code url
    df = df.assign( Chain_URL=chain_url_base_str + df['ChainCode'] )
    df = df.assign( Hotel_URL=hotel_url_base_str + df['HotelCode'] )
    
    # save a copy
    self.hotel_df = df
    # drop all columns other than HotelCode HotelName ChainCode ChainName Score Chain_URL Hotel_URL
    self.relevant_df = df.drop( columns=df.loc[0:1, 'SegmentCategory':'Room_Description'].columns.to_list() )
    
    ##################################
    # Page 1 : Chain data
    self.hotel_chain_df = \
      pd.merge(
        self.relevant_df.groupby(['ChainCode','ChainName','Chain_URL']).size().reset_index(name='Count'),
        self.relevant_df.groupby(['ChainCode','ChainName','Chain_URL']).mean().reset_index(),
        on=['ChainCode', 'ChainName', 'Chain_URL'] )
    self.total_chains = len(self.hotel_chain_df)
    ##################################
    # Page 2 : per Chain Hotel data
    self.per_chain_hotel_data = { }
    for chaincode in self.hotel_chain_df['ChainCode'].to_list():
      self.per_chain_hotel_data[chaincode] = {}
      self.per_chain_hotel_data[chaincode]["dataframe"] = \
        self.relevant_df.query("ChainCode == '{code}'".format(code=chaincode) )
    #self.hotel_chain_df.sort_values(by='Count')
    #################################
    # Page 3 : per hotel date will be fetched from hotel_df
    self.attributes_map = {}
    for attr in self.attributes:
      curr_count = 0
      for k,v in self.hotel_df[attr].value_counts().to_dict().items():
        if is_attr_invalid( k ):
          continue
        curr_count += v
      self.attributes_map[attr] = curr_count
    self.attr_df = pd.DataFrame( self.attributes_map.items(), columns=["attr","count"] )
    

###################################################
## Layout details follows -
###################################################
class pages( object ):
  def __init__(self):
    self.datastore = dataStore()
    ##################################
    # Navbar & content cache
    self.page_1 = None
    self.page_2 = {}
    self.page_3 = {}
  
  def Navbar_2( self,
              chain_df,
                label_column_name=None,
                url_column_name=None,
              dropdown_label=None):
    children = []
    if type(chain_df) is pd.core.frame.DataFrame:
      for t in chain_df[[label_column_name, url_column_name]].itertuples():
        children.append( { 'label' : t[1], 'value': t[2] } )
    dropdown_children = []
    if len(children):
      dropdown_children = [dbc.Form([dbc.FormGroup(
      [
          dbc.Label(dropdown_label, html_for="dropdown"),
          dcc.Dropdown(
              id="dropdown",
              searchable=True,
              options=children,
              #className="large",
              className="dash-bootstrap"
          ),
      ],
      className="dash-bootstrap"
      )],
      className="dash-bootstrap"
      )]
    return dbc.NavbarSimple(
        children=dropdown_children,
        brand="Home",
        brand_href="/",
        sticky="top",
        #fluid=True,
        color="warning",
        #dark=True,
        className="dash-bootstrap"
      )
  
  def Navbar( self,
              chain_df,
                label_column_name=None,
                url_column_name=None,
              dropdown_label=None):
    '''
    Generic navbar
    '''
    children = []
    if type(chain_df) is pd.core.frame.DataFrame:
      for t in chain_df[[label_column_name, url_column_name]].itertuples():
        children.append( dbc.DropdownMenuItem(
                            dbc.NavLink( t[1],href=t[2] ),
                            className="small",
                            #bs_size="sm" 
                            ),
                        )
        #children.append( dbc.DropdownMenuItem(divider=False, className="small") )
    dropdown_children = []
    if len(children):
      dropdown_children = [ dbc.DropdownMenu(
                              nav=True,
                              in_navbar=True,
                              label=dropdown_label,
                              children=children,
                              #className="small",
                              #bs_size="sm",
                              color="dark",
                              ) ]
    
    self.navbar = dbc.NavbarSimple(
        children=dropdown_children,
        brand="Home",
        brand_href="/",
        sticky="top",
        #fluid=True,
        color="warning",
        #dark=True,
        className="dash-bootstrap"
      )
    return self.navbar
  
  def _404(self):
    return html.Div(
      [
        self.Navbar(chain_df=None),
        dbc.Container( 
          [ dbc.Row( [dbc.Col([html.H2("404")])] ) ],
          className="mt-4"),
      ],
      className="dash-bootstrap"
    )
  
  # homepage or summary
  def display_page_1(self):
    if self.page_1:
      return self.page_1
    self.page_1 = html.Div([], className="dash-bootstrap") 
    # add nav bar
    self.page_1.children.append(
                          self.Navbar(
                              chain_df = self.datastore.hotel_chain_df.sort_values(by='ChainName'),
                              label_column_name = 'ChainName',
                              url_column_name   = 'Chain_URL',
                              dropdown_label    = 'Chain Names'
                            )
                          )
    # data tweak
    df_score = self.datastore.hotel_chain_df.sort_values(by='Score')
    # 1.1 score scatter graph
    scatter_data = [
                      
                      go.Scatter( x = df_score['ChainName'],
                                  y = df_score['Score'],
                                  text=df_score['Count'],
                                  name="Mean Score",
                                  marker_color=df_score['Score'],
                                ),
                    go.Scatter( x = df_score['ChainName'],
                                y = df_score['Score'],
                                mode = 'markers',
                                marker_color=df_score['Score'],
                                marker=dict( size=df_score['Count']/14  ),
                                text=df_score['Count'],
                                name="Num of properties",
                              ),
                    ]
    # 2. pie chart
    pie_data = [go.Pie( values  = df_score['Count'],
                        labels  = df_score['ChainName'],
                        hoverinfo='label+percent',
                        opacity=0.8,
                        name="Chain Names",
                        text=df_score['Count'],
                        marker_colors=[ 'rgb(56, 75, 126)',   'rgb(18, 36, 37)',
                                        'rgb(34, 53, 101)',   'rgb(36, 55, 57)',
                                        'rgb(6, 4, 4)',       'rgb(177, 127, 38)',
                                        'rgb(205, 152, 36)',  'rgb(99, 79, 37)',
                                        'rgb(129, 180, 179)', 'rgb(124, 103, 37)',
                                        'rgb(33, 75, 99)',    'rgb(79, 129, 102)',
                                        'rgb(151, 179, 100)', 'rgb(175, 49, 35)',
                                        'rgb(36, 73, 147)',   'rgb(146, 123, 21)',
                                        'rgb(177, 180, 34)',  'rgb(206, 206, 40)',
                                        'rgb(175, 51, 21)',   'rgb(35, 36, 21)',
                                        'rgb(33, 75, 99)',    'rgb(79, 129, 102)',
                                        'rgb(151, 179, 100)', 'rgb(175, 49, 35)',
                                        'rgb(36, 73, 147)'],
                      )]
    # add figures
    self.page_1.children.append(
                          dbc.Container(
                            [
                              #########################################
                              # add info
                              dbc.Row(
                              [
                                dbc.Col([
                                  dbc.Card(
                                    dbc.CardBody(
                                    #"This is some text within a card body"
                                    [
                                      html.H2( "Hotel Content Ranking", className="card-title" ),
                                      html.P("navigation on top row", className="card-text")
                                    ]
                                    ),style={
                                        #'width':'75%',
                                        #'margin':25,
                                        'textAlign': 'center'},
                                    className="dash-bootstrap",
                                    color="dark", inverse=True
                                  ),
                                  dbc.Card(
                                  dbc.CardBody(
                                   html.H4(
                                    "There are total {} hotels under {} chains".format(
                                      self.datastore.total_hotels, self.datastore.total_chains
                                    ), className="card-title"
                                    ),
                                  ),
                                    style={
                                      #'width':'75%',
                                      #'margin':50,
                                      'textAlign': 'center'},
                                  className="dash-bootstrap",
                                  color="secondary", inverse=True
                                ),
                                ],
                                #width={"size": 6, "offset": 4}
                                ),
                              ]
                              ,
                                no_gutters=True,
                                align="start",
                                className="dash-bootstrap",
                              ),
                              
                              #########################################
                              # scatter graph
                              dbc.Row(
                                [
                                  dbc.Col([
                                    dcc.Graph(
                                      figure = {
                                        'data': scatter_data,
                                        'layout': go.Layout(
                                          title = 'Chain Attribute Score',
                                          xaxis = {'tickangle' : 45 },
                                          yaxis = {'title': 'Attr Score'},
                                          hovermode = 'closest',
                                          margin = dict(t=40, b=90, l=25, r=0),
                                          #yaxis_zeroline=False,
                                          #xaxis_zeroline=False,
                                        )
                                      },
                                      className="dash-bootstrap",
                                    )],
                                    #md=4,
                                    #width="auto",
                                    className="dash-bootstrap",
                                  ),
                                ],
                                no_gutters=True,
                                align="start",
                                className="dash-bootstrap",
                              ),
                              #########################################
                              dbc.Row([dbc.Col([html.H1()])]),
                              # pie chart
                              dbc.Row([
                                dbc.Col([
                                  dcc.Graph(
                                    figure = {
                                      'data': pie_data,
                                      'layout': go.Layout(
                                        margin = dict(t=40, b=100, l=0, r=0),
                                        title  = "Property distribution",
                                      )
                                    },
                                    className="dash-bootstrap",
                                  )],
                                  className="dash-bootstrap",
                                ),
                              ],
                              className="dash-bootstrap",
                              no_gutters=True,
                              align="start",
                              ),
                            ],
                            className="dash-bootstrap",
                            fluid=True,
                          ),
                        )
    return self.page_1
  
  # per chain page
  def display_page_2(self, chaincode ):
    '''
    datastore.per_chain_hotel_data is dict
    '''
    # try cache
    if chaincode in self.page_2:
      return self.page_2[chaincode]
    if chaincode not in self.datastore.per_chain_hotel_data:
      return self._404()
    # tweak data
    df_score = self.datastore.per_chain_hotel_data[chaincode]["dataframe"].sort_values(by='Score')
    # create & cache
    page = html.Div([
      self.Navbar(
                  chain_df = pd.concat( [ df_score.tail(10), df_score.head(10) ] ), # top & bottom combined
                  #chain_df = df_score.sample( len(df_score) ), # Random sampling, can set to len
                  #chain_df = df_score, # everything
                  label_column_name = 'HotelName',
                  url_column_name   = 'Hotel_URL',
                  dropdown_label    = 'Hotel Names'
                 ),
    ],
    className="dash-bootstrap")
    # add content
    # 1. hotel score scatter graph
    scatter_data = [go.Scatter( x = df_score['HotelName'],
                                y = df_score['Score'],
                                mode = 'lines',
                                marker = {
                                  'color'     : 'sandybrown',
                                  #'showscale' : True,
                                  #'colorscale': [[0, '#FAEE1C'], [0.33, '#F3558E'], [0.66, '#9C1DE7'], [1, '#581B98']],
                                  'size'      : 8,
                                },
                              )]
    page.children.append(
      dbc.Container(
        [
          # add info
          dbc.Row(
          [
            dbc.Col([
              dbc.Card(
              dbc.CardBody(
              #"This is some text within a card body"
               html.H2(
                "There are total {} hotels under {} chain".format(
                  len(df_score), self.datastore.chain_2_name_map.get(chaincode,chaincode)),
                ),
              ),
                style={
                  #'width':'75%',
                  #'margin':25,
                  'textAlign': 'center'},
              className="dash-bootstrap",
              color="dark", inverse=True
            ),
            ],
            #width={"size": 6, "offset": 4}
            ),
          ]
          ,
            no_gutters=True,
            align="start",
            className="dash-bootstrap",
          ),
          # graph 1
          dbc.Row([
            dbc.Col(
            [
              # scatter graph
              dcc.Graph(
                          figure = {
                            'data': scatter_data,
                            'layout': go.Layout(
                              title = 'Hotel Attribute Score',
                              xaxis = {'tickangle' : 45, 'title' : 'Hotel Name', 'tickfont' : dict( size=6) },
                              yaxis = {'title': 'Attr Score'},
                              hovermode = 'closest',
                              #margin = dict(t=40, b=0, l=0, r=0),
                            )
                          }
                        )
            ],
            className="dash-bootstrap",
            )
          ],
          align="start",
          no_gutters=True,
          className="dash-bootstrap",
          ),
        ],
        fluid=True,
        className="dash-bootstrap",
      )
    )
    self.page_2[chaincode] = page
    return page
  
  ##################################################################
  # per hotel page, private function
  def _get_attrs_table(self, avail_attrs, unavail_attrs, type_str ):
    #########################
    # 1. Create table header
    table_pie_header_unavail = "{} Attributes Unavailable".format( type_str )
    table_pie_header_avail  = "{} Attributes Available".format( type_str )
    table_header = [
      html.Thead(
        html.Tr(
          [
            html.Th(table_pie_header_avail),
            html.Th(table_pie_header_unavail),
          ]
        ),
        className="dash-bootstrap",
      ),
    ]
    #########################
    # 2. fill table rows
    available_attr_len = len(avail_attrs)
    not_available_attr_len = len(unavail_attrs)
    #########################
    table_rows = []
    for i in range(0, max( available_attr_len, not_available_attr_len ) ):
      row = []
      if avail_attrs:
        row.append( html.Td(avail_attrs.pop(0)) )
      else:
        row.append( html.Td("") )
      if unavail_attrs:
        row.append( html.Td(unavail_attrs.pop(0)) )
      else:
        row.append( html.Td("") )
      table_rows.append( html.Tr(row) )
    return dbc.Table(
                      table_header + [html.Tbody(table_rows)],
                      bordered=True,
                      hover=True,
                      responsive=True,
                      striped=True,
                    )
  ##################################################################
  # Pie chart
  def _get_attrs_pie(self, available_len, not_available_len, type_str ):
    table_pie_header_unavail = "{} Attributes Unavailable".format( type_str )
    table_pie_header_avail  = "{} Attributes Available".format( type_str )
    pie_data = [go.Pie( values  = [ available_len, not_available_len, ],
                        labels  = ['<b>'+table_pie_header_avail+'</b>', '<b>'+table_pie_header_unavail+'</b>'],
                        hoverinfo='label+value',
                        opacity=0.8,
                        textfont=dict(size=20),
                        marker_colors=[ 'rgb(151, 179, 100)', 'rgb(175, 49, 35)' ],
                      )]
    return dcc.Graph(
                      figure = {
                        'data': pie_data,
                        'layout': go.Layout(
                         margin = dict(t=40, b=40, l=0, r=0),
                         title  = "{} Attribute distribution".format( type_str ),
                        )
                      },
                      style={'height': '450px', 'width' : '620px'},
                      className="dash-bootstrap",
                    )
  
  # per hotel page
  def display_page_3(self, hotelcode ):
    # try cache
    if hotelcode in self.page_3:
      return self.page_3[hotelcode]
    
    # get hotel data
    curr_hotel_df = self.datastore.hotel_df.query( "HotelCode == '{}'".format( hotelcode ) )
    # check for not exitent data
    if curr_hotel_df.empty:
      return self._404()
    # sieving out irrelevant columns ( 'Chain_URL', 'Hotel_URL' )
    curr_hotel_df = curr_hotel_df.drop( columns=curr_hotel_df.columns[-2:] )
    ########################################################################
    # 1. fill table rows data
    # collate items
    available_room_attr = []
    available_hotel_attr = []
    not_available_room_attr = []
    not_available_hotel_attr = []
    for k,v in curr_hotel_df.to_dict().items():
      if is_hotel_attr( k ):
        if is_attr_invalid( str(v.values()) ):
          not_available_hotel_attr.append( k )
        else:
          available_hotel_attr.append( k )
      else:
        if is_attr_invalid( str(v.values()) ):
          not_available_room_attr.append( k )
        else:
          available_room_attr.append( k )
    #############################
    not_available_hotel_attr_len = len(not_available_hotel_attr)
    not_available_room_attr_len  = len(not_available_room_attr)
    total_attr_absent            = not_available_hotel_attr_len+not_available_room_attr_len
    
    available_hotel_attr_len     = len(available_hotel_attr)
    available_room_attr_len      = len(available_room_attr)
    total_attr_present           = available_hotel_attr_len+available_room_attr_len
    #########################
    # 2. create page
    # 2.1 jumbotron
    jumbotron = dbc.Jumbotron(
      [
      dbc.Container(
        [
          html.H1( curr_hotel_df.HotelName.to_list()[0], className="display-3"),
          html.P( "Falls under " + curr_hotel_df.ChainName + " which has " + 
                  str(
                    len(
                      self.datastore.per_chain_hotel_data[curr_hotel_df.ChainCode.to_list()[0]]['dataframe']
                      )) +
                  " more listed properties",
                className="lead",
          ),
          html.Hr(className="my-2"),
          html.P(
            "Out of {total} attributes {absent} are absent.".format( total =total_attr_absent, absent = total_attr_present )
          ),
          html.P(
            ""
          ),
        ],
        fluid=True,
        className="h-100 p-5 text-white bg-dark rounded-3",
      ),
      ],
      fluid=True,
    )
    #######################################
    # 2.2 Create 2 Tabs for room & hotel
    # Card 1 for hotel attr
    card_1 =  dbc.Container(
    [
      dbc.Row( [
        dbc.Col(
          [
            self._get_attrs_table( available_hotel_attr, not_available_hotel_attr, "Hotel"),
          ],
        ),
        dbc.Col(
          [
            self._get_attrs_pie(available_hotel_attr_len, not_available_hotel_attr_len, "Hotel"),
          ],
        ),
      ],
      className="dash-bootstrap",
      no_gutters=True,
      align="start",
      ),
    ],
    className="dash-bootstrap",
    fluid=True,
    )
    ## Card 2 room attrs
    card_2 =dbc.Container(
    [
      dbc.Row( [
        dbc.Col(
          [
            self._get_attrs_table( available_room_attr, not_available_room_attr, "Room"),
          ],
        ),
        dbc.Col(
          [
            self._get_attrs_pie(available_room_attr_len, not_available_room_attr_len, "Hotel"),
          ],
        ),
      ],
      className="dash-bootstrap",
      no_gutters=True,
      align="start",
      ),
    ],
    className="dash-bootstrap",
    fluid=True,
    )
    # combined tabs
    tabs_view = dbc.Tabs(
    [
      dbc.Tab(
        card_1,
        label="Hotel attribute details",
        labelClassName="text-warning"
      ),
      dbc.Tab(
        card_2,
        label="Room attribute details",
        labelClassName="text-warning"
      ),
    ],
    className="dash-bootstrap",
    )
    ###########################
    # 3. create & cache page
    page = html.Div([
        # empty menu for hotel
        self.Navbar(chain_df=None),
        
        # page header
        jumbotron,
        
        # tabs
        tabs_view,
    ],
    className="dash-bootstrap"
    )
    # create & cache
    self.page_3[hotelcode] = page
    return page

###############################################################
## Index / callable details
###############################################################
from dash.dependencies import Input, Output
from urllib.parse import urlparse, parse_qsl, urlencode
def decode_url( href ):
  # href example : http://127.0.0.1:8050/hotel?ChainCode=HL&ChainCode=BJS705
  parsed_href = urlparse( href )
  # we will return { 'ChainCode' : 'HL',   'HotelCode' : 'BJS705' }
  return { x[0] : x[1] for x in parse_qsl(parsed_href.query) }


app = dash.Dash(  __name__,   external_stylesheets=[dbc.themes.BOOTSTRAP], )

app.config.suppress_callback_exceptions = True

app.layout = html.Div([
    dcc.Location(id = 'url', refresh = False),
    html.Div(id = 'page-content', className="dash-bootstrap")
],
className="dash-bootstrap"
)

pageStore = pages()

#########################
# base index callable
@app.callback(
              Output('page-content', 'children'),
              [ Input('url', 'href') ]
              )
def display_page( href ):
    pathname = urlparse( href ).path
    print('Request', pathname, href )
    if pathname == '/':
        return pageStore.display_page_1( )
    elif pathname.count('/chain') == 1:
        attributes = decode_url( href )
        return pageStore.display_page_2( chaincode=attributes.get('ChainCode',None) )
    elif pathname.count('/hotel') == 1:
        attributes = decode_url( href )
        return pageStore.display_page_3( hotelcode=attributes.get('HotelCode',None) )
    else:
        return pageStore._404()

if __name__ == '__main__':
    app.run_server(debug=True)