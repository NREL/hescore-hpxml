Cooling
#######

.. contents:: Table of Contents

.. _primaryclgsys:

Determining the primary cooling system
**************************************

HEScore only allows the definition of one cooling system. If an HPXML document
contains more than one cooling system then the primary one must be chosen for
input into HEScore. The primary cooling system is determined according to the
following logic:

#. HPXML has a ``PrimaryCoolingSystem`` element that references with system
   is the primary one. If this is present, the properties of that referenced
   cooling system are translated into HEScore inputs.
#. If there is no defined primary cooling system in HPXML, each
   ``CoolingSystem`` or ``HeatPump`` is translated into HEScore inputs and
   systems with teh same ``type`` and ``efficiency_method`` are combined by
   taking a capacity weighted average of the ``efficiency`` or ``year``
   depending on the efficiency method. The combined system that has the
   greatest total capacity is then used for the HEScore inputs. 
#. Finally, if there is no ``CoolingSystem`` or ``HeatPump`` object, then the
   house is determined to not have a cooling system in HEScore. 

.. warning::

   The translation is not currently doing the weighted average of like systems 
   as described in the HEScore help.
   
Cooling system type
*******************

HPXML provides two difference HVAC system elements that can provide cooling:
``CoolingSystem`` that only provides cooling and ``HeatPump`` which can provide
heating and cooling. 

Heat Pump
=========

The ``HeatPump`` element in HPXML can represent either an air-source heat pump
or ground source heat pump in HEScore. Which is specified in HEScore is
determined by the ``HeatPumpType`` element in HPXML according to the following
mapping.

.. table:: Heat Pump Type mapping

   ============================  ============================
   HPXML Heat Pump Type          HEScore Cooling Type
   ============================  ============================
   water-to-air                  gchp
   water-to-water                gchp
   air-to-air                    heat_pump
   mini-split                    heat_pump
   ground-to-air                 gchp
   ============================  ============================

.. clg-sys_

Cooling System
==============

The ``CoolingSystem`` element in HPXML is used to describe any system that
provides cooling that is not a heat pump. The ``CoolingSystemType`` subelement
is used to determine what kind of cooling system to specify for HEScore. This
is done according to the following mapping.

.. table:: Cooling System Type mapping

   =========================  ====================
   HPXML Cooling System Type  HEScore Cooling Type
   =========================  ====================
   central air conditioning   split_dx
   room air conditioner       packaged_dx
   mini-split                 split_dx
   evaporative cooler         *not translated*
   other                      *not translated*
   =========================  ====================

.. note::
   
   If an HPXML cooling system type maps to *not translated* the translation
   will fail. 
   
   While HEScore does have evaporative coolers in the API, they are not fully
   implemented in the software and will not be used in the translation.

Cooling Efficiency
******************

Cooling efficiency can be described in HEScore by either the rated efficiency
(SEER, EER), or if that is unavailable, the year installed/manufactured from
which HEScore estimates the efficiency based on shipment weighted efficiencies
by year. The translator follows this methodology and looks for the rated
efficiency first and if it cannot be found sends the year installed. 

Rated Efficiency
================

HEScore expects efficiency to be described in different units depending on the
cooling system type. 

.. table:: HEScore cooling type efficiency units

   ===============  ================
   Cooling Type     Efficiency Units
   ===============  ================
   split_dx         SEER
   packaged_dx      EER
   heat_pump        SEER
   gchp             EER
   dec              *not applicable*
   iec              *not applicable*
   idec             *not applicable*
   ===============  ================

.. note::

   Currently evaporative coolers are disabled in the translation (see 
   :ref:`clg-sys`) and therefore do not need efficiency units specified.

The translator searches the ``CoolingSystem/AnnualCoolingEfficiency`` or
``HeatPump/AnnualCoolEfficiency`` elements of the primary cooling system and
uses the first one that has the correct units.

.. _clg-shipment-weighted-efficiency:

Shipment Weighted Efficiency
============================

When an appropriate rated efficiency cannot be found, HEScore can accept the
year the equipment was installed and estimate the efficiency based on that. The
year is retrieved from the ``YearInstalled`` element, and if that is not
present the ``ModelYear`` element. 


