Cooling
#######

.. contents:: Table of Contents

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

.. _clg-sys:

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
   evaporative cooler         split_dx
   other                      *not translated*
   =========================  ====================

.. note::
   
   If an HPXML cooling system type maps to *not translated* the translation
   will fail. 
   
   Evaporative coolers are approximated in HEScore by a high efficiency central
   air (``split_dx``) system.

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
   ===============  ================

The translator searches the ``CoolingSystem/AnnualCoolingEfficiency`` or
``HeatPump/AnnualCoolEfficiency`` elements of the primary cooling system and
uses the first one that has the correct units.

Evaporative coolers are always assumed to be a ``split_dx`` system with an
efficiency of SEER 28.

.. _clg-shipment-weighted-efficiency:

Shipment Weighted Efficiency
============================

When an appropriate rated efficiency cannot be found, HEScore can accept the
year the equipment was installed and estimate the efficiency based on that. The
year is retrieved from the ``YearInstalled`` element, and if that is not
present the ``ModelYear`` element. 


