Address and Requesting a New Session
####################################

.. contents:: Table of Contents

The first step in starting a HEScore transaction is to call the
``submit_address`` :term:`API` call.

Address
*******

The building address is found in HPXML under the ``Building/Site/Address``
element. The sub elements there easily translate into the expected address
format for HEScore. 

.. code-block:: xml

   <HPXML>
      ...
      <Building>
         <Site>
            <SiteID id="id1"/>
            <Address>
               <Address1>123 Main St.</Address1>
               <Address2></Address2>
               <CityMunicipality>Anywhere</CityMunicipality>
               <StateCode>CA</StateCode>
               <ZipCode>90000</ZipCode>
            </Address>
         </Site>      
      </Building>
   </HPXML>

HPXML allows for two lines of address elements. If both are used, the lines will
be concatenated with a space between for submission to the HEScore
``building_address.address`` field. All of the HPXML elements shown in the
above code snippet are required with the exception of ``Address2``

Assessment Type
***************

To begin a HEScore session an assement type must be selected. The assesment type
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
   +---------------------+-------------------------------------------+------------------------+
   |update               |*any*                                      |corrected               |
   +---------------------+-------------------------------------------+------------------------+
