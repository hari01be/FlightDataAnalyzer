import unittest

from datetime import datetime
from mock import Mock, patch

import numpy as np

from analysis.api_handler import NotFoundError
from analysis.node import (A, KeyPointValue, KeyTimeInstance, KPV, KTI, P, S,
                           Section)
from analysis.flight_attribute import (
    Approaches, LandingAirport, LandingRunway, TakeoffAirport, TakeoffRunway
    )

class TestTakeoffAirport(unittest.TestCase):
    def test_can_operate(self):
        self.assertEqual([('Liftoff', 'Latitude', 'Longitude')],
                         TakeoffAirport.get_operational_combinations())
        
        
    @patch('analysis.api_handler_http.APIHandlerHTTP.get_nearest_airport')
    def test_derive_airport_not_found(self, get_nearest_airport):
        '''
        Attribute is not set when airport is not found.
        '''
        get_nearest_airport.side_effect = NotFoundError('Not Found.')
        liftoff = KTI('Liftoff')
        liftoff.create_kti(1, 'STATE')
        latitude = P('Latitude', array=np.ma.masked_array([2.0,4.0,6.0]))
        longitude = P('Longitude', array=np.ma.masked_array([1.0,3.0,5.0]))
        takeoff_airport = TakeoffAirport()
        takeoff_airport.set_flight_attr = Mock()
        takeoff_airport.derive(liftoff, latitude, longitude)
        self.assertEqual(get_nearest_airport.call_args, ((4.0, 3.0), {}))
        self.assertFalse(takeoff_airport.set_flight_attr.called)
    
    @patch('analysis.api_handler_http.APIHandlerHTTP.get_nearest_airport')
    def test_derive_airport_found(self, get_nearest_airport):
        '''
        Attribute is set when airport is found.
        '''
        airport_info = {'id': 123}
        get_nearest_airport.return_value = airport_info
        liftoff = KTI('Liftoff')
        liftoff.create_kti(1, 'STATE')
        latitude = P('Latitude', array=np.ma.masked_array([2.0,4.0,6.0]))
        longitude = P('Longitude', array=np.ma.masked_array([1.0,3.0,5.0]))
        takeoff_airport = TakeoffAirport()
        takeoff_airport.set_flight_attr = Mock()
        takeoff_airport.derive(liftoff, latitude, longitude)
        self.assertEqual(get_nearest_airport.call_args,
                         ((4.0, 3.0), {}))
        self.assertEqual(takeoff_airport.set_flight_attr.call_args,
                         ((airport_info,), {}))


class TestTakeoffRunway(unittest.TestCase):
    def test_can_operate(self):
        '''
        There may be a neater way to test this, but at least it's verbose.
        '''
        expected = \
        [('Takeoff Airport', 'Takeoff Heading'),
         ('Takeoff Airport', 'Takeoff Heading', 'Liftoff'),
         ('Takeoff Airport', 'Takeoff Heading', 'Latitude'),
         ('Takeoff Airport', 'Takeoff Heading', 'Longitude'),
         ('Takeoff Airport', 'Takeoff Heading', 'Precise Positioning'),
         ('Takeoff Airport', 'Takeoff Heading', 'Liftoff', 'Latitude'),
         ('Takeoff Airport', 'Takeoff Heading', 'Liftoff', 'Longitude'),
         ('Takeoff Airport', 'Takeoff Heading', 'Liftoff', 
          'Precise Positioning'),
         ('Takeoff Airport', 'Takeoff Heading', 'Latitude', 'Longitude'),
         ('Takeoff Airport', 'Takeoff Heading', 'Latitude', 
          'Precise Positioning'),
         ('Takeoff Airport', 'Takeoff Heading', 'Longitude', 
          'Precise Positioning'),
         ('Takeoff Airport', 'Takeoff Heading', 'Liftoff', 'Latitude', 
          'Longitude'),
         ('Takeoff Airport', 'Takeoff Heading', 'Liftoff', 'Latitude',
          'Precise Positioning'),
         ('Takeoff Airport', 'Takeoff Heading', 'Liftoff', 'Longitude',
          'Precise Positioning'),
         ('Takeoff Airport', 'Takeoff Heading', 'Latitude', 'Longitude',
          'Precise Positioning'),
         ('Takeoff Airport', 'Takeoff Heading', 'Liftoff', 'Latitude',
          'Longitude', 'Precise Positioning')]
        self.assertEqual(TakeoffRunway.get_operational_combinations(),
                         expected)
    
    @patch('analysis.api_handler_http.APIHandlerHTTP.get_nearest_runway')
    def test_derive(self, get_nearest_runway):
        runway_info = {'ident': '27L', 'runways': [{'length': 20}]}
        get_nearest_runway.return_value = runway_info
        takeoff_runway = TakeoffRunway()
        takeoff_runway.set_flight_attr = Mock()
        # Airport and Takeoff Heading arguments.
        airport = A('Takeoff Airport')
        airport.value = {'id':25}
        takeoff_heading = KPV('Takeoff Heading')
        takeoff_heading.create_kpv(1, 20.0)
        takeoff_runway.derive(airport, takeoff_heading)
        self.assertEqual(get_nearest_runway.call_args, ((25, 20.0), {}))
        self.assertEqual(takeoff_runway.set_flight_attr.call_args,
                         ((runway_info,), {}))
        # Airport, Takeoff Heading, Liftoff, Latitude, Longitude and Precision
        # arguments. Latitude and Longitude are only passed with all these
        # parameters available and Precise Positioning is True.
        liftoff = KTI('Liftoff')
        liftoff.create_kti(1, 'STATE')
        latitude = P('Latitude', array=np.ma.masked_array([2.0,4.0,6.0]))
        longitude = P('Longitude', array=np.ma.masked_array([1.0,3.0,5.0]))
        precision = A('Precision')
        precision.value = True
        takeoff_runway.derive(airport, takeoff_heading, liftoff, latitude,
                              longitude, precision)
        self.assertEqual(get_nearest_runway.call_args, ((25, 20.0),
                                                        {'latitude': 4.0,
                                                         'longitude': 3.0}))
        self.assertEqual(takeoff_runway.set_flight_attr.call_args,
                         ((runway_info,), {}))
        # When Precise Positioning's value is False, Latitude and Longitude
        # are not used.
        precision.value = False
        takeoff_runway.derive(airport, takeoff_heading, liftoff, latitude,
                              longitude, precision)
        self.assertEqual(get_nearest_runway.call_args, ((25, 20.0), {}))
        self.assertEqual(takeoff_runway.set_flight_attr.call_args,
                         ((runway_info,), {}))
        

class TestApproaches(unittest.TestCase):
    def test_can_operate(self):
        # Can operate with approach lat lng.
        self.assertTrue(Approaches.can_operate(\
            ['Start Datetime',
             'Approach And Landing',
             'Heading At Landing',
             'Touch And Go',
             'Go Around',
             'Latitude At Low Point On Approach',
             'Longitude At Low Point On Approach']))
        # Can operate with landing lat lng.
        self.assertTrue(Approaches.can_operate(\
            ['Start Datetime',
             'Approach And Landing',
             'Heading At Landing',
             'Touch And Go',
             'Go Around',
             'Latitude At Landing',
             'Longitude At Landing']))
        # Can operate with everything.
        self.assertTrue(Approaches.can_operate(\
            ['Start Datetime',
             'Approach And Landing',
             'Heading At Landing',
             'Touch And Go',
             'Go Around',
             'Latitude At Low Point On Approach',
             'Longitude At Low Point On Approach',
             'Heading At Low Point On Approach',
             'Latitude At Landing',
             'Longitude At Landing',
             'Touch And Go',
             'Go Around']))
        # Cannot operate missing latitude.
        self.assertFalse(Approaches.can_operate(\
            ['Start Datetime',
             'Approach And Landing',
             'Heading At Landing',
             'Touch And Go',
             'Go Around',
             'Longitude At Low Point On Approach']))
        # Cannot operate missing Approach and Landing.
        self.assertFalse(Approaches.can_operate(\
            ['Start Datetime',
             'Heading At Landing',
             'Latitude At Low Point On Approach',
             'Longitude At Low Point On Approach']))
        # Cannot operate with differing sources of lat lng.
        self.assertFalse(Approaches.can_operate(\
            ['Start Datetime',
             'Approach And Landing',
             'Heading At Landing',
             'Touch And Go',
             'Go Around',
             'Latitude At Low Point On Approach',
             'Longitude At Landing']))
    
    def test__get_lat_lon(self):
        # Landing KPVs.
        approaches = Approaches()
        approach_slice = slice(3,10)
        landing_lat_kpvs = KPV('Latitude At Landing',
                               items=[KeyPointValue(1, 13, 'b'),
                                      KeyPointValue(5, 10, 'b'),
                                      KeyPointValue(17, 14, 'b')])
        landing_lon_kpvs = KPV('Longitude At Landing',
                               items=[KeyPointValue(1, -1, 'b'),
                                      KeyPointValue(5, -2, 'b'),
                                      KeyPointValue(17, 2, 'b')])
        lat, lon = approaches._get_lat_lon(approach_slice, landing_lat_kpvs,
                                           landing_lon_kpvs, None, None)
        self.assertEqual(lat, 10)
        self.assertEqual(lon, -2)
        # Approach KPVs.
        approach_slice = slice(10,15)
        approach_lat_kpvs = KPV('Latitude At Low Point On Approach',
                                items=[KeyPointValue(12, 4, 'b')])
        approach_lon_kpvs = KPV('Longitude At Low Point On Approach',
                                items=[KeyPointValue(12, 3, 'b')])
        lat, lon = approaches._get_lat_lon(approach_slice, None, None,
                                           approach_lat_kpvs, approach_lon_kpvs)
        self.assertEqual(lat, 4)
        self.assertEqual(lon, 3)
        # Landing and Approach KPVs, Landing KPVs preferred.
        approach_slice = slice(4, 15)
        lat, lon = approaches._get_lat_lon(approach_slice, landing_lat_kpvs,
                                           landing_lon_kpvs, approach_lat_kpvs,
                                           approach_lon_kpvs)
        self.assertEqual(lat, 10)
        self.assertEqual(lon, -2)
        approach_slice = slice(20,40)
        lat, lon = approaches._get_lat_lon(approach_slice, landing_lat_kpvs,
                                           landing_lon_kpvs, approach_lat_kpvs,
                                           approach_lon_kpvs)
        self.assertEqual(lat, None)
        self.assertEqual(lon, None)
    
    def test__get_hdg(self):
        approaches = Approaches()
        # Landing KPV
        approach_slice = slice(1,10)
        landing_hdg_kpvs = KPV('Heading At Landing',
                               items=[KeyPointValue(2, 30, 'a'),
                                      KeyPointValue(14, 40, 'b')])
        hdg = approaches._get_hdg(approach_slice, landing_hdg_kpvs, None)
        self.assertEqual(hdg, 30)
        # Approach KPV
        approach_hdg_kpvs = KPV('Heading At Landing',
                                items=[KeyPointValue(4, 15, 'a'),
                                       KeyPointValue(23, 30, 'b')])
        hdg = approaches._get_hdg(approach_slice, None, approach_hdg_kpvs)
        self.assertEqual(hdg, 15)
        # Landing and Approach KPV, Landing preferred
        hdg = approaches._get_hdg(approach_slice, landing_hdg_kpvs,
                                  approach_hdg_kpvs)
        self.assertEqual(hdg, 30)
        # No KPVs in slice.
        approach_slice = slice(30,60)
        hdg = approaches._get_hdg(approach_slice, landing_hdg_kpvs,
                                  approach_hdg_kpvs)
        self.assertEqual(hdg, None)
    
    def test__get_approach_type(self):
        approaches = Approaches()
        # Heading At Landing KPVs.
        landing_hdg_kpvs = KPV('Heading At Landing',
                               items=[KeyPointValue(9, 21, 'a')])
        approach_slice = slice(7, 10)
        approach_type = approaches._get_approach_type(approach_slice,
                                                      landing_hdg_kpvs, None,
                                                      None)
        self.assertEqual(approach_type, 'LANDING')
        # Touch and Go KTIs.
        touch_and_gos = KTI('Touch And Go', items=[KeyTimeInstance(12, 'a'),
                                                   KeyTimeInstance(16, 'a')])
        approach_slice = slice(8,14)
        approach_type = approaches._get_approach_type(approach_slice, None,
                                                      touch_and_gos, None)
        self.assertEqual(approach_type, 'TOUCH_AND_GO')
        # Go Around KTIs.
        go_arounds = KTI('Go Arounds', items=[KeyTimeInstance(12, 'a'),
                                              KeyTimeInstance(16, 'a')])
        approach_type = approaches._get_approach_type(approach_slice, None,
                                                      None, go_arounds)
        self.assertEqual(approach_type, 'GO_AROUND')
        # Heading At Landing and Touch And Gos, Heading preferred.
        approach_type = approaches._get_approach_type(approach_slice,
                                                      landing_hdg_kpvs,
                                                      touch_and_gos, None)
        self.assertEqual(approach_type, 'LANDING')
        # Heading At Landing and Go Arounds. Heading preferred.
        approach_type = approaches._get_approach_type(approach_slice,
                                                      landing_hdg_kpvs,
                                                      None, go_arounds)
        self.assertEqual(approach_type, 'LANDING')
        # Touch And Gos and Go Arounds. Touch And Gos preferred.
        approach_type = approaches._get_approach_type(approach_slice,
                                                      None, touch_and_gos,
                                                      go_arounds)
        self.assertEqual(approach_type, 'TOUCH_AND_GO')
        # All 3, Heading preferred.
        approach_type = approaches._get_approach_type(approach_slice,
                                                      landing_hdg_kpvs,
                                                      touch_and_gos, go_arounds)
        self.assertEqual(approach_type, 'LANDING')
        # No KPVs/KTIs within slice.
        approach_slice = slice(100, 200)
        approach_type = approaches._get_approach_type(approach_slice,
                                                      landing_hdg_kpvs,
                                                      touch_and_gos, go_arounds)
        self.assertEqual(approach_type, None)
        
    
    @patch('analysis.api_handler_http.APIHandlerHTTP.get_nearest_airport')
    @patch('analysis.api_handler_http.APIHandlerHTTP.get_nearest_runway')
    def test_derive(self, get_nearest_runway, get_nearest_airport):
        approaches = Approaches()
        approaches.set_flight_attr = Mock()
        # No approach type due to missing 'Touch And Go', 'Go Around' and
        # 'Heading At Landing' KTI/KPVs.
        start_datetime = A('Start Datetime', value=datetime(1970, 1,1))
        approach_and_landing = S('Approach and Landing',
                                 items=[Section('a', slice(0,10))])
        landing_lat_kpvs = KPV('Latitude At Landing',
                               items=[KeyPointValue(5, 10, 'b')])
        landing_lon_kpvs = KPV('Longitude At Landing',
                               items=[KeyPointValue(5, -2, 'b')])
        landing_hdg_kpvs = KPV('Heading At Landing',
                               items=[KeyPointValue(15, 60, 'a')])
        go_arounds = KTI('Go Around', items=[KeyTimeInstance(25, 'Go Around')])
        touch_and_gos = KTI('Touch And Go',
                            items=[KeyTimeInstance(35, 'Touch And Go')])
        approaches.derive(start_datetime, approach_and_landing,
                          landing_hdg_kpvs, touch_and_gos, go_arounds,
                          landing_lat_kpvs, landing_lon_kpvs, None, None, None,
                          None, None)
        self.assertEqual(approaches.set_flight_attr.call_args, (([],), {}))
        # Go Around KTI exists within slice.
        get_nearest_airport.return_value = {'id': 1}
        go_arounds = KTI('Go Around', items=[KeyTimeInstance(5, 'Go Around')])
        approaches.derive(start_datetime, approach_and_landing,
                          landing_hdg_kpvs, touch_and_gos, go_arounds,
                          landing_lat_kpvs, landing_lon_kpvs, None, None, None,
                          None, None)
        expected_datetime = datetime(1970, 1, 1, 0, 0,
                                     approach_and_landing[0].slice.stop) # 10 seconds offset.
        self.assertEqual(approaches.set_flight_attr.call_args,
                         (([{'airport': 1, 'type': 'GO_AROUND', 'runway': None,
                             'datetime': expected_datetime}],), {}))
        self.assertEqual(get_nearest_airport.call_args, ((10, -2), {}))
        # Touch And Go KTI exists within the slice.
        touch_and_gos = KTI('Touch And Go',
                            items=[KeyTimeInstance(5, 'Touch And Go')])
        go_arounds = KTI('Go Around', items=[KeyTimeInstance(25, 'Go Around')])
        approaches.derive(start_datetime, approach_and_landing,
                          landing_hdg_kpvs, touch_and_gos, go_arounds,
                          landing_lat_kpvs, landing_lon_kpvs, None, None, None,
                          None, None)
        expected_datetime = datetime(1970, 1, 1, 0, 0,
                                     approach_and_landing[0].slice.stop) # 10 seconds offset.
        self.assertEqual(approaches.set_flight_attr.call_args,
                         (([{'airport': 1, 'type': 'TOUCH_AND_GO', 
                             'runway': None, 'datetime': expected_datetime}],),
                          {}))
        self.assertEqual(get_nearest_airport.call_args, ((10, -2), {}))
        # Use 'Heading At Low Point Of Approach' to query for runway.
        get_nearest_runway.return_value = {'identifier': '06L'}
        approach_hdg_kpvs = KPV('Heading At Low Point Of Approach',
                                items=[KeyPointValue(5, 25, 'a'),
                                       KeyPointValue(12, 35, 'b')])
        approaches.derive(start_datetime, approach_and_landing,
                          landing_hdg_kpvs, touch_and_gos, go_arounds,
                          landing_lat_kpvs, landing_lon_kpvs, None, None,
                          approach_hdg_kpvs, None, None)
        self.assertEqual(approaches.set_flight_attr.call_args,
                         (([{'airport': 1, 'type': 'TOUCH_AND_GO', 
                             'runway': '06L', 'datetime': expected_datetime}],),
                          {}))
        self.assertEqual(get_nearest_airport.call_args, ((10, -2), {}))
        self.assertEqual(get_nearest_runway.call_args, ((1, 25), {}))
        # Landing Heading KPV exists within slice.
        touch_and_gos = KTI('Touch And Go',
                            items=[KeyTimeInstance(35, 'Touch And Go')])
        landing_hdg_kpvs = KPV('Heading At Landing',
                               items=[KeyPointValue(5, 60, 'a')])
        approaches.derive(start_datetime, approach_and_landing,
                          landing_hdg_kpvs, touch_and_gos, go_arounds,
                          landing_lat_kpvs, landing_lon_kpvs, None, None, None,
                          None, None)
        self.assertEqual(approaches.set_flight_attr.call_args,
                         (([{'airport': 1, 'type': 'LANDING', 
                             'runway': '06L', 'datetime': expected_datetime}],),
                          {}))
        self.assertEqual(get_nearest_airport.call_args, ((10, -2), {}))
        self.assertEqual(get_nearest_runway.call_args, ((1, 60), {}))
        # Do not use Latitude and Longitude when requesting runway if Precise
        # precisioning is False.
        precision = A('Precise Positioning', value=False)
        approaches.derive(start_datetime, approach_and_landing,
                          landing_hdg_kpvs, touch_and_gos, go_arounds,
                          landing_lat_kpvs, landing_lon_kpvs, None, None, None,
                          None, precision)
        self.assertEqual(approaches.set_flight_attr.call_args,
                         (([{'airport': 1, 'type': 'LANDING', 
                             'runway': '06L', 'datetime': expected_datetime}],),
                          {}))
        self.assertEqual(get_nearest_airport.call_args, ((10, -2), {}))
        self.assertEqual(get_nearest_runway.call_args, ((1, 60), {}))
        # Pass Latitude and Longitude into get_nearest_runway if 'Precise
        # Positioning' is True.
        precision.value = True
        approaches.derive(start_datetime, approach_and_landing,
                          landing_hdg_kpvs, touch_and_gos, go_arounds,
                          landing_lat_kpvs, landing_lon_kpvs, None, None, None,
                          None, precision)
        self.assertEqual(approaches.set_flight_attr.call_args,
                         (([{'airport': 1, 'type': 'LANDING', 
                             'runway': '06L', 'datetime': expected_datetime}],),
                          {}))
        self.assertEqual(get_nearest_airport.call_args, ((10, -2), {}))
        self.assertEqual(get_nearest_runway.call_args, ((1, 60),
                                                        {'latitude': 10,
                                                         'longitude': -2}))
        # Use Approach Lat Lon KPVs if available.
        approach_lat_kpvs = KPV('Latitude At Low Point On Approach',
                                items=[KeyPointValue(5, 8, 'b')])
        approach_lon_kpvs = KPV('Longitude At Low Point On Approach',
                                items=[KeyPointValue(5, 4, 'b')])
        approaches.derive(start_datetime, approach_and_landing,
                          landing_hdg_kpvs, touch_and_gos, go_arounds, None,
                          None, approach_lat_kpvs, approach_lon_kpvs, None,
                          None, precision)
        self.assertEqual(get_nearest_runway.call_args, ((1, 60),
                                                        {'latitude': 8,
                                                         'longitude': 4}))
        self.assertEqual(approaches.set_flight_attr.call_args,
                         (([{'airport': 1, 'type': 'LANDING', 
                             'runway': '06L', 'datetime': expected_datetime}],),
                          {}))
        # Prefer Landing Lat Lon KPVs if both Landing and Approach are provided.
        approaches.derive(start_datetime, approach_and_landing,
                          landing_hdg_kpvs, touch_and_gos, go_arounds,
                          landing_lat_kpvs, landing_lon_kpvs, approach_lat_kpvs,
                          approach_lon_kpvs, None, None, precision)
        self.assertEqual(get_nearest_runway.call_args, ((1, 60),
                                                        {'latitude': 10,
                                                         'longitude': -2}))
        self.assertEqual(approaches.set_flight_attr.call_args,
                         (([{'airport': 1, 'type': 'LANDING', 
                             'runway': '06L', 'datetime': expected_datetime}],),
                          {}))
        # Use 'ILS Frequency On Approach' to query for runway if available.
        precision.value = False
        approach_ilsfreq_kpvs = KPV('ILS Frequency on Approach',
                                    items=[KeyPointValue(5, 330150, 'b')])
        approaches.derive(start_datetime, approach_and_landing,
                          landing_hdg_kpvs, touch_and_gos, go_arounds,
                          landing_lat_kpvs, landing_lon_kpvs, approach_lat_kpvs,
                          approach_lon_kpvs, None, approach_ilsfreq_kpvs,
                          precision)
        self.assertEqual(get_nearest_runway.call_args, ((1, 60),
                                                        {'ilsfreq': 330150}))
        self.assertEqual(approaches.set_flight_attr.call_args,
                         (([{'airport': 1, 'type': 'LANDING', 
                             'runway': '06L', 'datetime': expected_datetime}],),
                          {}))
        # Airport cannot be found.
        get_nearest_airport.side_effect = NotFoundError('', '')
        approaches.derive(start_datetime, approach_and_landing,
                          landing_hdg_kpvs, touch_and_gos, go_arounds,
                          landing_lat_kpvs, landing_lon_kpvs, approach_lat_kpvs,
                          approach_lon_kpvs, None, approach_ilsfreq_kpvs,
                          precision)
        self.assertEqual(approaches.set_flight_attr.call_args, (([],), {}))
        # Runway cannot be found.
        get_nearest_runway.side_effect = NotFoundError('', '')
        approaches.derive(start_datetime, approach_and_landing,
                          landing_hdg_kpvs, touch_and_gos, go_arounds,
                          landing_lat_kpvs, landing_lon_kpvs, approach_lat_kpvs,
                          approach_lon_kpvs, None, approach_ilsfreq_kpvs,
                          precision)
        self.assertEqual(approaches.set_flight_attr.call_args, (([],), {}))


class TestLandingAirport(unittest.TestCase):
    def test_can_operate(self):
        self.assertEqual(LandingAirport.get_operational_combinations(),
                         [('Latitude At Landing', 'Longitude At Landing')])
    
    @patch('analysis.api_handler_http.APIHandlerHTTP.get_nearest_airport')
    def test_derive_airport_not_found(self, get_nearest_airport):
        '''
        Attribute is not set when airport is not found.
        '''
        get_nearest_airport.side_effect = NotFoundError('Not Found.')
        latitude = KPV('Latitude At Landing',
                       items=[KeyPointValue(12, 0.5, 'a'),
                              KeyPointValue(32, 0.9, 'a'),])
        longitude = KPV('Longitude At Landing',
                        items=[KeyPointValue(12, 7.1, 'a'),
                               KeyPointValue(32, 8.4, 'a')])
        landing_airport = LandingAirport()
        landing_airport.set_flight_attr = Mock()
        landing_airport.derive(latitude, longitude)
        self.assertEqual(get_nearest_airport.call_args, ((0.9, 8.4), {}))
        self.assertFalse(landing_airport.set_flight_attr.called)
    
    @patch('analysis.api_handler_http.APIHandlerHTTP.get_nearest_airport')
    def test_derive_airport_found(self, get_nearest_airport):
        '''
        Attribute is set when airport is found.
        '''
        airport_info = {'id': 123}
        latitude = KPV('Latitude At Landing',
                       items=[KeyPointValue(12, 0.5, 'a'),
                              KeyPointValue(32, 0.9, 'a'),])
        longitude = KPV('Longitude At Landing',
                        items=[KeyPointValue(12, 7.1, 'a'),
                               KeyPointValue(32, 8.4, 'a')])
        landing_airport = LandingAirport()
        landing_airport.set_flight_attr = Mock()
        landing_airport.derive(latitude, longitude)
        get_nearest_airport.return_value = airport_info
        landing_airport.set_flight_attr = Mock()
        landing_airport.derive(liftoff, latitude, longitude)
        self.assertEqual(get_nearest_airport.call_args, ((0.9, 8.4), {}))
        self.assertEqual(takeoff_airport.set_flight_attr.call_args,
                         ((airport_info,), {}))


#class TestLandingRunway(unittest.TestCase):
    #def test_can_operate(self):
        #self.assertTrue(False)
    
    #def test_derive(self):
        #self.assertTrue(False)


#class TestLandingRunway(unittest.TestCase):
    #def test_can_operate(self):
        #self.assertTrue(False)
    
    #def test_derive(self):
        #self.assertTrue(False)

