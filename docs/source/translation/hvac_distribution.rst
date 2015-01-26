HVAC Distribution
#################

.. contents:: Table of Contents

In HPXML multiple ``HVACDistribution`` elements can be associated with a heating
or cooling system. That element can then describe a ducted system, a hydronic
system, or an open ended other system. For the translation to HEScore, only
``HVACDistribution`` elements that are ducted are considered.

.. _ductlocationmapping:

Duct Location Mapping
*********************

For each ``Ducts`` element in each air distribution system, the location of the
duct mapped from HPXML enumerations to HEScore enumerations according to the
following mapping.

.. table:: Duct Location mapping

   ======================  ================
   HPXML                   HEScore
   ======================  ================
   conditioned space       cond_space
   unconditioned space     *not translated*
   unconditioned basement  uncond_basement
   unvented crawlspace     unvented_crawl
   vented crawlspace       vented_crawl
   crawlspace              *not translated*
   unconditioned attic     uncond_attic
   interstitial space      *not translated*
   garage                  *not translated*
   outside                 *not translated*
   ======================  ================

.. warning:: 

   If an HPXML duct location maps to *not translated* above, the 
   translation for the house will fail.

Aggregating Duct Fractions
**************************

For each air distribution system in HPXML the fraction of the ducting in each
HEScore location are added together. The duct fractions are summed across air
distribution systems by weighting them by the conditioned floor area served by
the air distribution system, if that's available. If there is no
``ConditionedFloorAreaServed`` element available, then the duct fractions
across each system are weighted equally.

.. note::

   Either all of the ``HVACDistribution`` elements must have a 
   ``ConditionedFloorAreaServed`` subelement or none of them must. If some have
   it and others do not, the translation will fail.

Duct Insulation
***************

If the any of the ``Ducts`` elements in a particular
:ref:`location <ductlocationmapping>` have a ``DuctInsulationRValue`` or
``DuctInsulationThickness`` that is greater than zero, all of the ducts in that
location are considered insulated.

Duct Sealing
************

Duct leakage measurements are not stored on the individual ``Ducts`` elements in
HEScore, which means they are not directly associated with a duct location.
They are instead associated with an ``AirDistribution`` element, which can have
many ducts in many locations. Duct sealing information is therefore associated
with all ducts in an ``AirDistribution`` element.

To specify that the ducts in an ``AirDistribution`` system are sealed, the
translator expects to find either of the following elements:

* ``DuctLeakageMeasurement/LeakinessObservedVisualInspection`` element with
  the value of "connections sealed w mastic".
* ``HVACDistribution/HVACDistributionImprovement/DuctSystemSealed`` element
  with the value of "true".

The ``DuctLeakageMeasurement`` can hold values for actual measurements of
leakage, but since HEScore cannot do anything with them, they will be ignored.
Therefore the following will result in an "unsealed" designation:

.. code-block:: xml

   <DuctLeakageMeasurement>
      <DuctType>supply</DuctType>
      <!-- All of this is ignored -->
      <DuctLeakageTestMethod>duct leakage tester</DuctLeakageTestMethod>
      <DuctLeakage>
          <Units>CFM25</Units>
          <Value>0.000000001</Value><!-- exceptionally low leakage -->
      </DuctLeakage>
   </DuctLeakageMeasurement>

and the following will result in a "sealed" designation:

.. code-block:: xml
   :emphasize-lines: 3

   <DuctLeakageMeasurement>
      <DuctType>supply</DuctType>
      <LeakinessObservedVisualInspection>connections sealed w mastic</LeakinessObservedVisualInspection>
   </DuctLeakageMeasurement>

When combining ducts in certain :ref:`locations <ductlocationmapping>` across
``HVACDistribution`` systems, the duct sealing designation for the systems in
the location that handle the largest area weighted by the percentage of the
ducts in a location will be used. For instance, if a home has air distribution
system (a.) that serves 2000 sq.ft. with 60% of its ducts in an unconditioned
basement that is sealed and system (b.) that serves 2500 sq.ft. that has 40% of
its ducts in an unconditioned basement that is *not* sealed, the ducts in the
unconditioned basement will be marked as sealed:

.. math::
   :nowrap:
   
   \begin{eqnarray*}
   \text{duct a} && \text{duct b} \\
   2000 \times 60\% && 2500 \times 40\% \\
   1200 &>& 1000
   \end{eqnarray*}






