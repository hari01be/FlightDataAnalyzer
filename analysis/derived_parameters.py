import logging
import numpy as np

from hdfaccess.parameter import P, Parameter

from analysis.node import DerivedParameterNode
from analysis.library import (align, hysteresis, interleave,
                              rate_of_change, straighten_headings)

from settings import HYSTERESIS_FPIAS, HYSTERESIS_FPROC

#-------------------------------------------------------------------------------
# Derived Parameters


# Q: What do we do about accessing KTIs - params['a kti class name'] is a list of kti's
#   - could have a helper - filter_for('kti_name', take_max=True) # and possibly take_first, take_min, take_last??

# Q: Accessing information like ORIGIN / DESTINATION

# Q: What about V2 Vref etc?


class AccelerationVertical(DerivedParameterNode):
    def derive(self, acc_norm=P('Acceleration Normal'), 
               acc_lat=P('Acceleration Lateral'), 
               acc_long=P('Acceleration Longitudinal'), 
               pitch=P('Pitch'), roll=P('Roll')):
        """
        Resolution of three accelerations to compute the vertical
        acceleration (perpendicular to the earth surface).
        """
        # Align the acceleration and attitude samples to the normal acceleration,
        # ready for combining them.
        # "align" returns an array of the first parameter aligned to the second.
        ax = align(acc_long, acc_norm) 
        pch = np.radians(align(pitch, acc_norm))
        ay = align(acc_lat, acc_norm) 
        rol = np.radians(align(roll, acc_norm))
        
        # Simple Numpy algorithm working on masked arrays
        resolved_in_pitch = ax * np.sin(pch) + acc_norm.array * np.cos(pch)
        self.array = resolved_in_pitch * np.cos(rol) - ay * np.sin(rol)
        

class AirspeedMinusVref(DerivedParameterNode):
    
    def derive(self, airspeed=P('Airspeed'), vref=P('Vref')):
        vref_aligned = align(vref, airspeed)
        self.array = airspeed.array - vref_aligned


class AltitudeAAL(DerivedParameterNode):
    name = 'Altitude AAL'
    def derive(self, alt_std=P('Altitude STD'), alt_rad=P('Radio Altitude')):
        return NotImplemented

    
class AltitudeRadio(DerivedParameterNode):
    # This function allows for the distance between the radio altimeter antenna
    # and the main wheels of the undercarriage.

    # The parameter raa_to_gear is measured in feet and is positive if the
    # antenna is forward of the mainwheels.
    
    def derive(self, alt_rad=P('Altitude Radio Sensor'),
               pitch=P('Pitch'), raa_to_gear=None):
        
        if raa_to_gear:
            # Align the pitch attitude samples to the Radio Altimeter samples,
            # ready for combining them.
            pch = np.radians(align(pitch, alt_rad))
            # Make an array which is a copy of the sensor data
            result = params['Altitude Radio Sensor'].array.copy()
            # Now apply the offset if one has been provided
            return result - np.sin(pch)*raa_to_gear
        else:
            return alt_rad # No difference except a change in name.

        
class AltitudeQNH(DerivedParameterNode):
    name = 'Altitude QNH'
    def derive(self):
        return NotImplemented


class AltitudeTail(DerivedParameterNode):
    # This function allows for the distance between the radio altimeter antenna
    # and the point of the airframe closest to tailscrape.
    
    # The parameter gear_to_tail is measured in feet and is the distance from 
    # the main gear to the point on the tail most likely to scrape the runway.
    def derive(self, alt_rad = P('Altitude Radio'), 
               pitch = P('Pitch')):
        # Align the pitch attitude samples to the Radio Altimeter samples,
        # ready for combining them.
        pch = np.radians(align(pitch, alt_rad))
        # Make an array which is a copy of the sensor data
        result = alt_rad.array.copy()
        # Now apply the offset
        self.array = result - np.sin(pch)*self.aircraft.model.dist_gear_to_tail
        

class DistanceToLanding(DerivedParameterNode):
    def derive(self, alt_aal = P('Altitude AAL'),
               gspd = P('Ground Speed'),
               ils_gs = P('Glideslope Deviation'),
               ldg = P('LandingAirport')):
        return NotImplemented
    

class FlapCorrected(DerivedParameterNode):
    def derive(self, flap=P('Flap')):
        return NotImplemented
    

class FlightPhaseAirspeed(DerivedParameterNode):  #Q: Rename to AirpseedHysteresis ?
    def derive(self, airspeed=P('Airspeed')):
        self.array = hysteresis(airspeed.array, HYSTERESIS_FPIAS)


class FlightPhaseRateOfClimb(DerivedParameterNode):
    def derive(self, alt = P('Altitude STD')):
        self.array = rate_of_change(alt, 4)
        
        #self.array = hysteresis(rate_of_change(alt, 4),
                                #HYSTERESIS_FPROC)


class HeadContinuous(DerivedParameterNode):
    def derive(self, head_mag=P('Heading Magnetic')):
        self.array = straighten_headings(head_mag.array)


class ILSLocaliserGap(DerivedParameterNode):
    def derive(self, ils_loc = P('Localiser Deviation'),
               alt_aal = P('Altitude AAL')):
        return NotImplemented

    
class ILSGlideslopeGap(DerivedParameterNode):
    def derive(self, ils_gs = P('Glideslope Deviation'),
               alt_aal = P('Altitude AAL')):
        return NotImplemented
 
    
'''

This is ex-AGS and I don't know what it does or if we need/want this. DJ

class ILSValLim(DerivedParameterNode):
    # Taken from diagram as: ILS VAL/LIM -- TODO: rename!
    dependencies = [LocaliserGap, GlideslopeGap]
    def derive(self, params):
        return NotImplemented
'''

class MACH(DerivedParameterNode):
    def derive(self, ias = P('Airspeed'),
               tat = P('TAT'), alt = P('Altitude Std')):
        return NotImplemented
        

class RateOfClimb(DerivedParameterNode):
    def derive(self, alt_std = P('Altitude STD'),):
               ##alt_rad = P('Altitude Radio')):
        #TODO: Needs huge rewrite but this might work for starters. DJ
        self.array = rate_of_change(alt_std, 1)

class Relief(DerivedParameterNode):
    # also known as Terrain
    
    # Quickly written without tests as I'm really editing out the old dependencies statements :-(
    def derive(self, alt_aal = P('Altitude AAL'),
               alt_rad = P('Radio Altitude')):
        altitude = align(alt_aal, alt_rad)
        self.array = altitude - alt_rad

'''

Better done together

class SmoothedLatitude(DerivedParameterNode):
    dependencies = ['Latitude', 'True Heading', 'Indicated Airspeed'] ##, 'Altitude Std']
    def derive(self, params):
        return NotImplemented
    
class SmoothedLongitude(DerivedParameterNode):
    dependencies = ['Longitude', 'True Heading', 'Indicated Airspeed'] ##, 'Altitude Std']
    def derive(self, params):
        return NotImplemented
'''

class TrueAirspeed(DerivedParameterNode):
    dependencies = ['SAT', 'VMO', 'MMO', 'Indicated Airspeed', 'Altitude QNH']
    def derive(self, ias = P('Airspeed'),
               alt_std = P('Altitude STD'),
               sat = P('SAT')):
        return NotImplemented
    
class TrueHeading(DerivedParameterNode):
    # Requires the computation of a magnetic deviation parameter linearly 
    # changing from the deviation at the origin to the destination.
    def derive(self, head = P('Heading Continuous'),
               dev = P('Magnetic Deviation')):
        dev_array = align(dev, head)
        self.array = head + dev_array
    

class RateOfTurn(DerivedParameterNode):
    dependencies = [HeadContinuous]
    def derive(self, head = P('Head Continuous')):
        self.array = rate_of_change(head, 1)


class Pitch(DerivedParameterNode):
    def derive(self, p1=P('Pitch (1)'), p2=P('Pitch (2)')):
        self.hz = p1.hz * 2
        self.offset = min(p1.offset, p2.offset)
        self.array = interleave (p1, p2)

                
class AltitudeRadio(DerivedParameterNode):
    # This function allows for the distance between the radio altimeter antenna
    # and the main wheels of the undercarriage.

    # The parameter raa_to_gear is measured in feet and is positive if the
    # antenna is forward of the mainwheels.
    
    dependencies = ['Altitude Radio Sensor','Pitch']
    def derive(self, params, raa_to_gear):
        # Align the pitch attitude samples to the Radio Altimeter samples,
        # ready for combining them.
        pch = np.radians(align(params['Pitch'], params['Altitude Radio Sensor']))
        # Now apply the offset
        self.array = params['Altitude Radio Sensor'].array - np.sin(pch)*raa_to_gear
        
        
class AltitudeTail(DerivedParameterNode):
    # This function allows for the distance between the radio altimeter antenna
    # and the point of the airframe closest to tailscrape.
    
    # The parameter gear_to_tail is measured in feet and is the distance from 
    # the main gear to the point on the tail most likely to scrape the runway.
    
    dependencies = ['Altitude Radio','Pitch']
    def derive(self, params, gear_to_tail):
        # Align the pitch attitude samples to the Radio Altimeter samples,
        # ready for combining them.
        pch = np.radians(align(params['Pitch'], params['Altitude Radio']))
        # Now apply the offset
        self.array = params['Altitude Radio'].array - np.sin(pch)*gear_to_tail
