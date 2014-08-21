Roof and Attic
##############

.. contents:: Table of Contents

HPXML allows the specification of multiple ``Attic`` elements each of which
relates to a ``Roof`` element. That relation is optional in HPXML, but is
required when translating to HEScore, because it is important to know which
roof relates to each attic space. An area is required for each ``Attic``
element if there is more than one ``Attic`` element.

.. _rooftype:

Attic/Roof Type
***************

Each ``Attic`` is considered and the ``AtticType`` is mapped into a HEScore roof
type according to the following mapping.

.. table:: HPXML Attic Type to HEScore Roof type mapping

   =====================  ================
   HPXML                  HEScore
   =====================  ================
   cape cod               cath_ceiling
   cathedral ceiling      cath_ceiling
   flat roof              cath_ceiling
   unvented attic         cond_attic
   vented attic           vented_attic
   venting unknown attic  *not translated*
   other                  *not translated*
   =====================  ================

.. warning:: 

   Items that are *not translated* will result in a translation error. 
   Would it be reasonable to assume that "venting unknown attic" is a vented attic?
   
The roof type that has the largest total area is entered into HEScore since it
can only accept one roof type. The properties of the ``Attic`` elements with
the same roof type are combined. For variables with a discrete selection the
value that covers the greatest combined area is used. For R-values a UA
calculation is performed to determine the equivalent overall R-value for the
attic. This is discussed in more detail in :ref:`rvalues`.

Roof Color
**********

Roof color in HEScore is mapped from the HPXML ``Roof/RoofColor`` element
according to the following mapping.

.. table:: HPXML to HEScore roof color mapping

   ==========  =======
   HPXML       HEScore
   ==========  =======
   light       light
   medium      medium
   dark        dark
   reflective  white
   ==========  =======

.. warning::

   HEScore allows for more detailed roof color descriptions than HPXML. 
   There is no way in HPXML to specify the following HEScore roof colors:
   
   - medium_dark
   - cool_color (along with the absorptivity, which is also missing an HPXML element.)

Exterior Finish
***************

HPXML stores the exterior finish information in the ``Roof/RoofType`` element.
This is translated into the HEScore exterior finish variable according to the
folling mapping.

.. table:: HPXML Roof Type to HEScore Exterior Finish mapping

   =================================  ====================
   HPXML                              HEScore
   =================================  ====================
   shingles                           composition shingles
   slate or tile shingles             concrete tile
   wood shingles or shakes            wood shakes
   asphalt or fiberglass shingles     tar and gravel
   metal surfacing                    *not translated*
   expanded polystyrene sheathing     *not translated*
   plastic/rubber/synthetic sheeting  *not translated*
   concrete                           concrete tile
   cool roof                          *not translated*
   green roof                         *not translated*
   no one major type                  *not translated*
   other                              *not translated*
   =================================  ====================
   
.. warning::

   Items where the HEScore translation indicates *not translated* above 
   will result in a translation error. Also, I'm not sure if "asphalt or 
   fiberglass shingles" should be translated to composition shingles, but if I 
   do that there's no enumeration that maps to tar and gravel.

Rigid Foam Sheathing
********************

If the ``AtticRoofInsulation`` element has a ``Layer`` with the "continuous"
``InstallationType``, ``InsulationMaterial/Rigid``, and a ``NominalRValue``
greater than zero, the roof is determined to have rigid foam sheathing and one
of the construction codes is selected accordingly. Otherwise one of the
standard wood frame construction codes is selected.

.. code-block:: xml
   :emphasize-lines: 8-12

   <Attic>
       <SystemIdentifier id="attic5"/>
       <AttachedToRoof idref="roof3"/>
       <AtticType>cathedral ceiling</AtticType>
       <AtticRoofInsulation>
           <SystemIdentifier id="attic5roofins"/>
           <Layer>
               <InstallationType>continuous</InstallationType>
               <InsulationMaterial>
                   <Rigid>eps</Rigid>
               </InsulationMaterial>
               <NominalRValue>10</NominalRValue>
           </Layer>
       </AtticRoofInsulation>
       <Area>2500</Area>
   </Attic>

Radiant Barrier
***************

If the ``Roof/RadiantBarrier`` element exists and has a "true" value, the attic
is assumed to have a radiant barrier and no roof deck insulation is assumed
according to the construction codes available in HEScore.

.. _rvalues:

R-values
********

R-values for each the attic floor and roof deck are added up by summing the
values of the ``Layer/NominalRValue`` elements. When multiple attics must be
combined into a single construction code in HEScore, the R-value of the
combined attic is calculated using a *UA* calculation and an equivalent R-value
is determined.

.. math::

   UA_{total} = \frac{A_1}{R_1} + \frac{A_2}{R_2} + \dotsb

.. math::

   R_{total} = \frac{A_{total}}{UA_{total}}

Since HEScore only allows for certain discrete R-values in their construction
codes, the nearest R-value to the calculated one is selected. 


 