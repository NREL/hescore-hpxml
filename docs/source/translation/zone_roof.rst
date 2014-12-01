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
   unvented attic         vented_attic
   vented attic           vented_attic
   venting unknown attic  vented_attic
   other                  *not translated*
   =====================  ================

.. warning:: 

   Items that are *not translated* will result in a translation error.
   
The roof type that has the largest total area is entered into HEScore since it
can only accept one roof type. The properties of the ``Attic`` elements with
the same roof type are combined. For variables with a discrete selection the
value that covers the greatest combined area is used. For R-values a UA
calculation is performed to determine the equivalent overall R-value for the
attic. This is discussed in more detail in :ref:`roof-rvalues`.

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

.. note::

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
   asphalt or fiberglass shingles     composition shingles
   metal surfacing                    composition shingles
   expanded polystyrene sheathing     *not translated*
   plastic/rubber/synthetic sheeting  tar and gravel
   concrete                           concrete tile
   cool roof                          *not translated*
   green roof                         *not translated*
   no one major type                  *not translated*
   other                              *not translated*
   =================================  ====================
   
.. note::

   Items where the HEScore translation indicates *not translated* above 
   will result in a translation error. 

.. _rigid-sheathing:

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

.. _roof-rvalues:

Roof R-value
************

R-values for the roof deck are added up by summing the values of the
``Layer/NominalRValue`` elements where the layer is not :ref:`rigid-sheathing`.
If the house has more than one ``Attic`` element with roof insulation, the
insulation values are combined by first selecting the nearest roof
center-of-cavity R-value for each roof area from the table below.

.. table:: Roof Center-of-Cavity Effective R-values

   +-------------------+---------------------+------------+----------+--------------+---------------+
   |Exterior           |Composition or Metal |Wood Shakes |Clay Tile |Concrete Tile |Tar and Gravel |
   +-------------------+---------------------+------------+----------+--------------+---------------+
   |R-value            |Effective R-value                                                           |
   +===================+=====================+============+==========+==============+===============+
   | **Standard**                                                                                   |
   +-------------------+---------------------+------------+----------+--------------+---------------+
   |R-0                |2.7                  |3.2         |2.2       |2.3           |2.3            |
   +-------------------+---------------------+------------+----------+--------------+---------------+
   |R-11               |13.6                 |14.1        |13.2      |13.2          |13.2           |
   +-------------------+---------------------+------------+----------+--------------+---------------+
   |R-13               |15.6                 |16.1        |15.2      |15.2          |15.2           |
   +-------------------+---------------------+------------+----------+--------------+---------------+
   |R-15               |17.6                 |18.1        |17.2      |17.2          |17.2           |
   +-------------------+---------------------+------------+----------+--------------+---------------+
   |R-19               |21.6                 |22.1        |21.2      |21.2          |21.2           |
   +-------------------+---------------------+------------+----------+--------------+---------------+
   |R-21               |23.6                 |24.1        |23.2      |23.2          |23.2           |
   +-------------------+---------------------+------------+----------+--------------+---------------+
   |R-27               |#N/A                 |30.1        |29.2      |29.2          |29.2           |
   +-------------------+---------------------+------------+----------+--------------+---------------+
   | **w/ Radiant Barrier**                                                                         |
   +-------------------+---------------------+------------+----------+--------------+---------------+
   |R-0                |5                    |5.5         |4.5       |4.6           |4.6            |
   +-------------------+---------------------+------------+----------+--------------+---------------+
   | **w/ foam sheeting**                                                                           |
   +-------------------+---------------------+------------+----------+--------------+---------------+
   |R-0                |6.8                  |7.3         |6.4       |6.4           |6.4            |
   +-------------------+---------------------+------------+----------+--------------+---------------+
   |R-11               |17.8                 |18.3        |17.4      |17.4          |17.4           |
   +-------------------+---------------------+------------+----------+--------------+---------------+
   |R-13               |19.8                 |20.3        |19.4      |19.4          |19.4           |
   +-------------------+---------------------+------------+----------+--------------+---------------+
   |R-15               |21.8                 |22.3        |21.4      |21.4          |21.4           |
   +-------------------+---------------------+------------+----------+--------------+---------------+
   |R-19               |#N/A                 |26.3        |25.4      |25.4          |25.4           |
   +-------------------+---------------------+------------+----------+--------------+---------------+
   |R-21               |#N/A                 |28.3        |27.4      |27.4          |27.4           |
   +-------------------+---------------------+------------+----------+--------------+---------------+

Then a weighted average is calculated weighting the values by area. 

.. math::
   
   R_{eff,avg} = \frac{\sum_i R_{eff,i} A_i}{\sum_i A_i}

The R-0 effective center-of-cavity R-value (:math:`R_{offset}`) is selected for
the highest weighted roof construction type represented in the calculation and
is subtracted from :math:`R_{eff,avg}`. 

.. math::

   R = R_{eff,avg} - R_{offset}

Finally the R-value is rounded to the nearest insulation level in the
enumeration choices for the highest weighted roof construction type included in
the calculation.

Attic R-value
*************
 
Determining the attic floor insulation levels uses the same procedure as
:ref:`roof-rvalues` except the lookup table is different. The attic floor
center-of-cavity R-values are each R-0.5 greater than the nominal R-values in
the enumeration list. 

If the primary roof type is determined to be a cathedral ceiling, then an attic
R-value is not calculated.
