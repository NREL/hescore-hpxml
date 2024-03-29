About
#####

.. contents:: Table of Contents

.. _assessment-type-mapping:

Assessment Type
***************

To begin a HEScore session an assessment type must be selected. The assessment type
is determined from HPXML via the
``XMLTransactionHeaderInformation/Transaction`` and
``Building/ProjectStatus/EventType`` element using the following mapping: 

.. table:: Assessment Type mapping

   +---------------------+-------------------------------------------+------------------------+
   |XML Transaction Type |HPXML Event Type                           |HEScore Assessment Type |
   +=====================+===========================================+========================+
   |create               |audit                                      |initial                 |
   +                     +-------------------------------------------+------------------------+
   |                     |proposed workscope                         |alternative             |
   +                     +-------------------------------------------+------------------------+
   |                     |approved workscope                         |alternative             |
   +                     +-------------------------------------------+------------------------+
   |                     |construction-period testing/daily test out |test                    |
   +                     +-------------------------------------------+------------------------+
   |                     |job completion testing/final inspection    |final                   |
   +                     +-------------------------------------------+------------------------+
   |                     |quality assurance/monitoring               |qa                      |
   +                     +-------------------------------------------+------------------------+
   |                     |preconstruction                            |preconstruction         |
   +---------------------+-------------------------------------------+------------------------+
   |update               |*any*                                      |corrected               |
   +---------------------+-------------------------------------------+------------------------+

Assessment Date
***************

HEScore requires an assessment date. If a date is stored in the element
``Building/ProjectStatus/Date``, that date is used. If not, the current date is
used.

Building Dwelling Unit Type
***************************

HEScore requires specifying whether the building is a detached house, a town
house, an apartment unit, or a manufactured house through their ``building.dwelling_unit_type`` input. 
HPXML can specify this (and a variety of other house types) through the
``Building/BuildingSummary/BuildingConstruction/ResidentialFacilitytype`` data
element. Not all facility types in HPXML can be modeled in HEScore. The table
below shows how the possible enumerations of the HPXML field are translated
into HEScore. 

.. table:: HPXML Facility Types to HEScore Building Dwelling Unit Type

   ============================  ======================
   HPXML                         HEScore 
   ============================  ======================
   single-family detached        single_family_detached
   single-family attached        single_family_attached
   manufactured home             manufactured_home
   2-4 unit building             *not translated*
   5+ unit building              *not translated*
   multi-family - uncategorized  *not translated*
   multi-family - town homes     single_family_attached
   multi-family - condos         *not translated*
   apartment unit                apartment_unit
   studio unit                   *not translated*
   other                         *not translated*
   unknown                       *not translated*
   ============================  ======================

.. note::

   For enumerations that are *not translated*
   the HPXML file will fail to run in HEScore.
   ``Building/BuildingDetails/BuildingSummary/Site/Surroundings`` is no longer used for shared walls mapping in town houses.
   Each ``Wall`` is considered and the ``ExteriorAdjacentTo`` is mapped into a HEScore ``adjacent_to``.
   See :ref:`wall_exterior_adjacent_to`

Manufactured Home Sections
**************************

HEScore requires specifying manufactured home sections if ``building.dwelling_unit_type`` is a manufactured_home. 
HPXML can specify this through the 
``Building/BuildingDetails/BuildingSummary/BuildingConstruction/extension/ManufacturedHomeSections`` element.

.. note::

   ``CrossMod`` manufactured home will be treated as a single-family detached home in Hescore.  

Year Built, Stories, Bedrooms, Floor Height, and Floor Area
***********************************************************

The HEScore inputs ``year_built``, ``number_bedrooms``,
``num_floor_above_grade``, ``floor_to_ceiling_height``, and
``conditioned_floor_area`` are each retrieved from their corresponding HPXML
elements shown below.

.. code-block:: xml

   <HPXML>
      ...
      <Building>
        ... 
        <BuildingDetails>
            <BuildingSummary>
                <BuildingConstruction>
                    <YearBuilt>1998</YearBuilt>
                    <ConditionedFloorArea>2400</ConditionedFloorArea>
                    <NumberofConditionedFloorsAboveGrade>2</NumberofConditionedFloorsAboveGrade>
                    <AverageCeilingHeight>8</AverageCeilingHeight>
                    <NumberofBedrooms>3</NumberofBedrooms>
                </BuildingConstruction>
            </BuildingSummary>
        </BuildingDetails>
      </Building>
   </HPXML>

The HEScore input ``floor_to_ceiling_height`` will be calculated by dividing
``ConditionedBuildingVolume`` by ``ConditionedFloorArea`` if
``AverageCeilingHeight`` is omitted.

.. _house-orientation:

House Orientation
*****************

In HPXML the orientation of a house and orientations in general can be specified
as either a compass direction ('North','Southwest',etc.) or an azimuth measured
in degrees clockwise from North. HEScore requires a compass direction for the
orientation of the front of the house. If the azimuth is available in
``Building/BuildingDetails/BuildingSummary/Site/AzimuthOfFrontOfHome`` the
nearest compass direction is chosen. If the azimuth is omitted from HPXML but
the ``OrientationOfFronOfHome`` element exists, the orientation is used. 

Infiltration
************

HPXML allows the specification of multiple
``Building/BuildingDetails/Enclosure/AirInfiltration/AirInfiltrationMeasurement``
elements, which can contain either a blower door test or a qualitative
assessment of "leakiness". HPXML also allows the specification of multiple
``Building/BuildingDetails/Enclosure/AirInfiltration/AirSealing`` elements, 
which can contain a qualitative assessment of "leakiness".
Either of the elements above is required.
HEScore can be used with either a measurement from a
blower door test or by specifying  whether the house has been air sealed or
not (boolean). Preference is given to a blower door test measurement when it
is available in HPXML. 

.. _blower-door-test:

Blower Door Test
================
The translator first looks for an ``AirInfiltrationMeasurement`` with units
of :term:`CFM50`. If more than one of the ``AirInfiltrationMeasurement``
elements have units in :term:`CFM50`, the last one to appear in the document is
used. If there are no measurements in :term:`CFM50`, it will look for one in
:term:`ACH50`. If more than one of the ``AirInfiltrationMeasurement`` elements
have units in :term:`ACH50`, the last one to appear in the document is used. If
the ``UnitofMeasure`` element has a value of ACH, then the value is converted
to CFM using the building volume calculated by the floor area and floor height.

An example of the minimum expected elements in HPXML follows:

.. code-block:: xml

   <AirInfiltrationMeasurement>
      <SystemIdentifier id="infilt1"/>
      <HousePressure>50</HousePressure><!-- Must be 50 -->
      <BuildingAirLeakage>
         <UnitofMeasure>CFM<!-- or ACH --></UnitofMeasure>
         <AirLeakage>1234</AirLeakage>
      </BuildingAirLeakage>
   </AirInfiltrationMeasurement>
   
Air Sealing Present
===================

When a blower door test is not available the translator looks for an
``AirInfiltrationMeasurement`` or ``AirSealing`` that specifies an estimate of leakage. 
An example of the minimum expected elements in that case looks like:

.. code-block:: xml

   <AirInfiltrationMeasurement>
      <SystemIdentifier id="infilt2"/>
      <LeakinessDescription>tight</LeakinessDescription>
   </AirInfiltrationMeasurement>

.. code-block:: xml

   <AirSealing>
      <SystemIdentifier id="infilt3"/>
   </AirSealing>

If more than one ``AirInfiltrationMeasurement`` is found that have the above
elements, the last one to appear in the document is used. Whether the house is
marked as having air sealing present is determined according to the following
mapping from ``LeakinessDescription``:

.. table:: HPXML LeakinessDescription to HEScore Air Sealing Present

   =====================  ===================
   Leakiness Description  Air Sealing Present
   =====================  ===================
   very tight             True
   tight                  True
   average                False
   leaky                  False
   very leaky             False
   =====================  ===================

If ``AirSealing`` is found, the enclosure of the house is assumed to be air-sealed. 

Comments
********

The hpxml-hescore translator allows passing through comments. Since there's no equivalent way to communicate this
information in HPXML under the ``Building`` node, the translator will look for a specifically named element in ``extension``
of ``Building``:

.. code-block:: xml

    <Building>
        <extension>
            <Comments>Any comment</Comments>
        </extension>
    </Building>


If there's no comment found in ``extension`` element, the translator will look for the ``Project/ProjectDetails/Notes``
element for comments. Only the first ``Project`` node will be selected. For complicated cases
where buildings are assigned to multiple projects, using the extension element is recommended.