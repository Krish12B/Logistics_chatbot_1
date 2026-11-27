#!/usr/bin/env python3
"""Builds a long knowledge-base CSV for the FleetHarbor shipment chatbot.

Usage:
    python3 generate_kb.py [output.csv] [original.csv]

Defaults: writes kb_long.csv and reads kb_1.csv, both in this script's folder.

The output keeps every original row and adds generated rows, so the file has
more than MIN_ROWS rows in total. Company facts (hubs, delivery windows, booking
time, dispatch cutoff, claim window, hazmat zone, e-way bill limit, escalation
levels) come from the original rows. Everything else is general logistics
guidance. Review and edit the lists below before the file goes live.
"""
import csv
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUTPUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "kb_long.csv"
ORIGINAL = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "kb_1.csv"

MIN_ROWS = 2000
LAST_UPDATED = "2026-11-01"
FIELDS = ["doc_id", "category", "section_title", "content", "tags", "last_updated"]

HUBS = ["Ahmedabad", "Vadodara", "Rajkot"]

# (city, state). Gujarat destinations are intra-state from the hubs; the rest are inter-state.
DESTINATIONS = [
    ("Ahmedabad", "Gujarat"), ("Vadodara", "Gujarat"), ("Rajkot", "Gujarat"),
    ("Surat", "Gujarat"), ("Anand", "Gujarat"), ("Nadiad", "Gujarat"),
    ("Bharuch", "Gujarat"), ("Jamnagar", "Gujarat"), ("Bhavnagar", "Gujarat"),
    ("Gandhinagar", "Gujarat"), ("Mehsana", "Gujarat"), ("Gandhidham", "Gujarat"),
    ("Morbi", "Gujarat"), ("Junagadh", "Gujarat"), ("Porbandar", "Gujarat"),
    ("Valsad", "Gujarat"), ("Navsari", "Gujarat"), ("Bhuj", "Gujarat"),
    ("Palanpur", "Gujarat"), ("Godhra", "Gujarat"),
    ("Mumbai", "Maharashtra"), ("Pune", "Maharashtra"),
    ("Nashik", "Maharashtra"), ("Nagpur", "Maharashtra"),
    ("Indore", "Madhya Pradesh"), ("Bhopal", "Madhya Pradesh"),
    ("Jaipur", "Rajasthan"), ("Udaipur", "Rajasthan"), ("Jodhpur", "Rajasthan"),
    ("Delhi", "Delhi"), ("Gurugram", "Haryana"), ("Chandigarh", "Chandigarh"),
    ("Lucknow", "Uttar Pradesh"), ("Kanpur", "Uttar Pradesh"),
    ("Bengaluru", "Karnataka"), ("Chennai", "Tamil Nadu"), ("Coimbatore", "Tamil Nadu"),
    ("Hyderabad", "Telangana"), ("Kolkata", "West Bengal"),
    ("Bhubaneswar", "Odisha"), ("Raipur", "Chhattisgarh"),
    ("Dehradun", "Uttarakhand"), ("Kochi", "Kerala"),
]

# Delivery windows from CO-002 in the original knowledge base.
WINDOW = {"intra": "2 to 4", "inter": "4 to 7"}

# Goods families used for lane articles: (label, handling note, claim evidence note).
LANE_FAMILIES = [
    ("electronic goods",
     "Keep units in their original boxes with anti-static packing, and never stack heavy cartons on electronics.",
     "For a damage claim, photograph the carton and the unit, and keep the serial number from the invoice."),
    ("garments",
     "Pack in polybags with a moisture barrier, and keep cartons away from chemicals and food.",
     "Count pieces against the packing list at delivery and write any shortage on the POD."),
    ("ambient pharmaceuticals",
     "Keep batch numbers visible on every carton, store away from direct sunlight and heat, and send the batch certificate with the invoice.",
     "Record batch and expiry details on the POD, and report any broken tamper seal before signing."),
    ("perishable food",
     "Pick perishables FEFO, and confirm any temperature requirement at booking before dispatch.",
     "If product is spoiled, note the condition on the POD, and raise a claim with photos and the invoice within 7 days."),
    ("packaged FMCG goods",
     "Stack cartons by SKU with labels facing out, respect the stacking limit printed on each carton, and check expiry dates at receiving.",
     "Note any crushed or wet cartons on the POD and keep them until the claim is closed."),
    ("auto and machinery parts",
     "Secure heavy parts with straps or blocking so they do not shift, and mark the weight on each carton.",
     "Check for shifted or cracked parts at delivery, and record the part numbers on the POD."),
    ("ceramic tiles and glassware",
     "Use edge protectors and partition cartons, mark cartons FRAGILE on all sides, and load them upright where possible.",
     "Photos are mandatory for fragile goods at delivery (see DP-002), so take them before signing."),
]

# Commodity profiles: (name, packing, storage, labelling, documents, main risk).
PROFILES = [
    ("Mobile phones and laptops",
     "in their retail boxes inside a double-walled carton with corner protection",
     "in a dry, dust-free bin in Zone A, away from direct sunlight",
     "with the model number and serial range on the outer carton",
     "a commercial invoice with IMEI or serial details, and a packing list",
     "theft and pilferage"),
    ("Home appliances",
     "with foam or thermocol inserts that stop the unit moving inside the carton",
     "in a dry bin, kept upright where the carton design allows",
     "with upright arrows on every side and the model number",
     "an invoice, a packing list and a copy of the warranty card",
     "dropping and crushing"),
    ("Garments and readymade clothing",
     "in polybags with a moisture barrier, folded flat inside cartons",
     "in a dry area, away from chemicals and food",
     "with style, size and piece count on each carton",
     "an invoice with the HSN code and a packing list showing the piece count",
     "moisture and handling damage"),
    ("Fabric rolls",
     "wrapped in kraft paper or polybag, then strapped",
     "on pallets, off the floor, in a dry bin",
     "with the lot number and roll length",
     "an invoice, a packing list and any quality certificate supplied",
     "water damage and soiling"),
    ("Ambient pharmaceuticals",
     "in sealed inner packs inside a tamper-evident outer carton",
     "in a dry, temperature-stable area away from direct sunlight",
     "with batch number, manufacturing date and expiry date on every carton",
     "an invoice, a batch certificate and a packing list",
     "tampering and heat exposure"),
    ("Cold-chain pharmaceuticals",
     "in validated insulated packaging with the coolant packs agreed at booking",
     "only in the temperature-controlled area, with the temperature log kept",
     "with the storage temperature and the cold-chain symbol",
     "an invoice, a batch certificate and written cold-chain instructions",
     "spoilage if the temperature drifts"),
    ("Fresh fruit and vegetables",
     "in ventilated crates or cartons that allow airflow",
     "in the cold area, picked FEFO with the shortest shelf life first",
     "with product name, grade and packing date",
     "an invoice, a packing list and a phytosanitary certificate where the destination requires one",
     "bruising and rot"),
    ("Frozen food",
     "in insulated cartons with the dry ice or gel packs agreed at booking",
     "in the freezer area, and never refrozen after thawing",
     "with the storage temperature, use-by date and FSSAI license number",
     "an invoice and a packing list",
     "thawing during handling"),
    ("Dairy products",
     "in leak-proof containers inside sealed cartons",
     "in the chilled area, picked FEFO",
     "with product name, batch and expiry date",
     "an invoice, a packing list and the FSSAI license number on the label",
     "spoilage and leakage"),
    ("Packaged FMCG goods",
     "in shrink-wrapped multipacks inside sturdy cartons",
     "stacked by SKU on pallets",
     "with SKU, batch and expiry date on each carton",
     "an invoice, a packing list and an e-way bill where applicable",
     "pilferage and crushed cartons"),
    ("Two-wheeler and car spare parts",
     "in boxes with part-number labels and inner dividers",
     "in bins by part number, with fast movers in Zone A",
     "with part number, quantity and weight",
     "an invoice that lists part numbers, and a packing list",
     "wrong-part dispatch and shortages"),
    ("Machinery parts and tools",
     "in wooden or heavy cartons with metal strapping",
     "on pallets, with the heaviest items at the bottom",
     "with gross weight, a centre-of-gravity arrow and handling marks",
     "an invoice, a packing list and any test certificate supplied",
     "load shifting during transit"),
    ("Steel pipes and bars",
     "bundled and strapped, with edge protection",
     "on racks or floor pallets in the yard, kept dry",
     "with grade, size and bundle weight",
     "an invoice, a packing list and a mill test certificate",
     "bending and rust in wet weather"),
    ("Ceramic tiles",
     "in cartons with corner protectors and partition boards",
     "upright on pallets, never stacked above the carton limit",
     "with design, batch and box count, plus a FRAGILE mark",
     "an invoice and a packing list showing the box count",
     "breakage and edge chipping"),
    ("Glassware and crockery",
     "in cartons with cell dividers and paper or foam padding",
     "in a dry area, with cartons marked upright",
     "with a FRAGILE mark on all sides and an upright arrow",
     "an invoice and a packing list showing the piece count",
     "breakage"),
    ("Flat-pack furniture",
     "in corrugated sleeves with corner protection, wrapped in stretch film",
     "in bulk storage, stacked within the carton limit",
     "with the item code and the number of cartons per item",
     "an invoice and a packing list showing cartons per item",
     "scratching and corner damage"),
    ("Paper and stationery",
     "in moisture-proof wrapping inside cartons",
     "in a dry area, away from water sources",
     "with product type, ream count and carton weight",
     "an invoice and a packing list",
     "moisture and crushing"),
    ("Books and printed material",
     "in tied bundles or cartons, wrapped against moisture",
     "dry and off the floor",
     "with title, edition and copies per carton",
     "an invoice and a packing list showing the copy count",
     "water damage and bent corners"),
    ("Toys and children's products",
     "in sealed inner packs with safety information and age labels",
     "in a dry bin, kept apart from chemicals",
     "with the age grade and any safety marks the product requires",
     "an invoice, a packing list and a compliance certificate where the category requires one",
     "damage to inner packs and missing parts"),
    ("Cosmetics and personal care",
     "in sealed inner boxes with leak protection",
     "in a cool, dry area away from heat",
     "with batch number, manufacturing date and expiry date",
     "an invoice and a packing list, plus the ingredient sheet if the client supplies one",
     "leakage and heat damage"),
    ("Food grains and pulses",
     "in clean, stitched and labelled bags with moisture protection",
     "on pallets in a dry area, rotated FIFO or FEFO as set",
     "with grain type, net weight and lot number",
     "an invoice, a packing list and any quality or fumigation certificate supplied",
     "moisture, pests and weight loss"),
    ("Spices and masalas",
     "in airtight pouches inside cartons",
     "in a cool, dry area away from strong-smelling goods",
     "with product, net weight, batch and expiry date",
     "an invoice, a packing list and FSSAI details on the label",
     "aroma loss and moisture"),
    ("Cement and building material bags",
     "palletised and shrink-wrapped",
     "covered and off the ground",
     "with grade and weight per bag",
     "an invoice and a packing list showing the bag count",
     "moisture hardening and split bags"),
    ("Non-hazardous chemicals",
     "in sealed containers with leak-proof closures",
     "in a separate area, away from food and textile goods",
     "with product name, batch and handling marks",
     "an invoice, a packing list and a safety data sheet (SDS)",
     "leakage and cross-contamination"),
    ("Dangerous goods such as lithium batteries",
     "only in packaging approved for dangerous goods",
     "only in Zone H, the hazardous storage area",
     "with the hazard class label and UN number",
     "a dangerous goods declaration, an SDS and the carrier's valid hazmat certificate",
     "fire and regulatory non-compliance"),
]

# Eight angles per commodity. Placeholders come from PROFILES.
ASPECT_KEYS = ["packing", "storage", "labelling", "documents", "transport", "damage", "receiving", "delivery"]
ASPECTS = [
    ("Packing {n}",
     "Pack {n} {pack}. Inspect every carton at the packing station and do not dispatch cartons with crushed corners or open seals."),
    ("Storing {n} in the warehouse",
     "Store {n} {storage}. Record the bin location in the WMS at put-away, as set out in WO-002."),
    ("Labelling {n}",
     "Label {n} {label}. Labels must stay readable at the packing station and on the dock."),
    ("Documents for {n}",
     "Prepare {docs} for every dispatch of {n}. Dispatch stays blocked until the mandatory documents are attached (see SP-003)."),
    ("Transporting {n}",
     "The main transit risk for {n} is {risk}. Secure cartons on the vehicle so they cannot shift, and report any change in carton condition at the dock."),
    ("Preventing damage to {n}",
     "To prevent damage to {n}, watch closely for {risk}. Use trolleys or forklifts for heavy cartons, and never throw or drop them during loading."),
    ("Receiving {n} at the warehouse",
     "Check inbound {n} against the ASN and inspect the packaging. Report any unit discrepancy above 2 percent to the Warehouse Manager within 4 hours (see WO-001)."),
    ("Delivering {n}",
     "At delivery, record the condition of each carton of {n} on the POD. Photos are mandatory for fragile goods (see DP-002)."),
]

# Document guides: (name, what it is, when it is required, checks before dispatch).
DOCUMENTS = [
    ("Commercial invoice",
     "The seller's bill to the buyer, showing the goods, quantities, unit prices and total value.",
     "Needed for almost every dispatch, both domestic and export, and used to declare the value.",
     "Check that the consignee name, HSN code, quantities and value match the packing list."),
    ("Packing list",
     "A document listing each carton's contents, weight and dimensions.",
     "Required with every dispatch so the consignee can verify what arrived.",
     "Check that the carton count and total weight match the physical cartons."),
    ("E-way bill",
     "A GST document, identified by a 12-digit number, that tracks goods moving by road.",
     "Required for consignments valued above INR 50,000 under GST rules.",
     "Check that the e-way bill is valid for the route and that the vehicle number is correct."),
    ("Delivery challan",
     "A GST document issued when goods move without a sale, such as for job work or a branch transfer.",
     "Needed when stock moves between locations or goes out for processing.",
     "Check that the challan lists the goods, quantities and purpose of movement."),
    ("Tax invoice",
     "A GST invoice that shows the tax charged on a supply of goods.",
     "Issued when goods are sold to a registered buyer.",
     "Check the GSTIN, the tax rate and the invoice number."),
    ("Bill of lading",
     "A sea freight document that acts as a receipt for cargo and as evidence of the shipping contract.",
     "Issued by the ocean carrier for every sea shipment.",
     "Check that the shipper, consignee, notify party and port names match the booking."),
    ("Airway bill",
     "The air cargo document issued by the airline or forwarder for a consignment.",
     "Required for every air shipment.",
     "Check the AWB number, the number of pieces and the chargeable weight."),
    ("Certificate of origin",
     "A document that states the country where the goods were made.",
     "Needed for export shipments that claim preferential duty under a trade agreement.",
     "Check that the country of origin matches the goods and the invoice."),
    ("Import Export Code (IEC)",
     "The identity code issued by DGFT that is required for importing and exporting.",
     "Needed for any import or export transaction.",
     "Check that the IEC on the shipping bill or bill of entry is correct."),
    ("Bill of entry",
     "The customs declaration filed for imported goods.",
     "Needed to clear imported goods through customs.",
     "Check that HS codes, values and duty details match the commercial invoice."),
    ("Shipping bill",
     "The customs declaration filed for exported goods.",
     "Needed to clear exported goods through customs.",
     "Check that the export details match the invoice and packing list."),
    ("Insurance certificate",
     "A document proving that the goods are insured for transit.",
     "Needed when extended cover is bought at booking (see PO-001).",
     "Check that the insured value and policy period cover the shipment."),
    ("Safety data sheet (SDS)",
     "A document that describes a chemical's hazards, handling, storage and emergency measures.",
     "Required for chemicals and dangerous goods.",
     "Check that the SDS matches the product and is attached to the dispatch."),
    ("Certificate of analysis (CoA)",
     "A quality certificate that shows the test results for a batch.",
     "Needed when a buyer asks for proof of batch quality, which is common for pharmaceuticals and chemicals.",
     "Check that the batch number on the CoA matches the cartons."),
    ("Batch certificate",
     "A document confirming that a batch was released by the manufacturer.",
     "Needed for pharmaceutical shipments.",
     "Check that the batch numbers on the certificate match the cartons."),
    ("Mill test certificate",
     "A certificate from the steel mill showing the material grade and test results.",
     "Needed for steel shipments when the buyer asks for it.",
     "Check that the heat numbers on the certificate match the bundles."),
    ("Fumigation certificate",
     "A certificate confirming that goods were treated against pests.",
     "Needed when the destination or client requires pest-free proof, which is common for food grains.",
     "Check the treatment date and method on the certificate."),
    ("Phytosanitary certificate",
     "A plant health certificate confirming that plant produce is free of listed pests.",
     "Needed for some plant and produce exports where the destination requires it.",
     "Check the issuing authority and the consignment details."),
    ("Warranty card",
     "A card that shows the product's warranty terms and proof of purchase.",
     "Included with electronics and appliances when the manufacturer supplies it.",
     "Check that the serial number on the card matches the carton."),
    ("Goods receipt note (GRN)",
     "A warehouse record confirming that goods were received and checked.",
     "Created at receiving for every inbound consignment.",
     "Check that the received quantities and any discrepancy are recorded."),
    ("Pro forma invoice",
     "A preliminary invoice sent before the final invoice, often to agree terms or arrange payment.",
     "Used before an export order is confirmed.",
     "Check that it is marked pro forma and is replaced by the commercial invoice at dispatch."),
    ("Dock receipt",
     "A receipt issued by a port or container terminal when a container is accepted.",
     "Used for container shipments handed over at a terminal.",
     "Check that the container number and seal number match the booking."),
    ("Gate pass",
     "A pass that allows a vehicle or person to enter or leave a site.",
     "Used at warehouse and port gates.",
     "Check the vehicle number and the date on the pass."),
    ("Weighment slip",
     "A slip showing the weight of a loaded vehicle, recorded at a weighbridge.",
     "Needed when a load weight must be confirmed for billing or compliance.",
     "Check the vehicle number and the gross and tare weights."),
    ("Dangerous goods declaration",
     "A signed declaration that a consignment is correctly classified, packed and labelled as dangerous goods.",
     "Required for every dangerous goods shipment.",
     "Check the UN number, hazard class and packing group."),
    ("ISPM 15 wood packaging mark",
     "A stamp showing that wooden packaging was heat-treated or fumigated to international standards.",
     "Needed for export shipments that use wooden pallets or crates.",
     "Check that the stamp is visible on the wood."),
    ("Quality inspection report",
     "A report from an inspection of goods before shipment.",
     "Requested by the buyer or client for high-value or regulated goods.",
     "Check the inspection date and the lot or batch covered."),
    ("Authorisation letter",
     "A letter that authorises a person or company to collect or clear goods.",
     "Needed when someone other than the consignee collects the goods.",
     "Check the signatory and the validity date."),
    ("Delivery order",
     "A document that authorises release of goods from a warehouse, port or terminal.",
     "Used when goods leave a warehouse or terminal under a release order.",
     "Check the order number, consignee and quantities."),
    ("Proof of delivery (POD)",
     "The signed record that goods reached the consignee (see TM-003).",
     "Required for every completed delivery.",
     "Check that the receiver's name, signature or OTP and timestamp are captured."),
]

# Tracking events: (event, meaning, what to do, what happens next).
EVENTS = [
    ("Booking Confirmed", "The shipment is booked and an LR number is generated for tracking.",
     "Keep the LR number, because the carrier uses it too.", "A pickup is scheduled with the assigned carrier."),
    ("Pickup Scheduled", "A carrier has been assigned to collect the goods on a set day.",
     "Make sure someone at the pickup address can hand over the goods.", "The carrier collects the goods and the status changes."),
    ("Pickup Attempted", "The carrier reached the pickup address but could not collect the goods.",
     "Check that the goods are ready and that the contact person is reachable.", "A new pickup is scheduled."),
    ("Picked Up", "The carrier has collected the goods from the shipper.",
     "No action is needed unless the carton count is wrong.", "The goods move to the origin hub."),
    ("Received at Origin Hub", "The goods reached the origin warehouse and are being checked in.",
     "Nothing is needed. You can check the tracking page at any time.", "The goods are packed, sealed and labelled."),
    ("Packed and Sealed", "The cartons are packed, weighed and labelled at the packing station.",
     "No action is needed.", "The cartons are loaded onto the vehicle."),
    ("Loaded on Vehicle", "The cartons are loaded and the vehicle number is recorded.",
     "Keep the vehicle number for reference.", "The vehicle departs the origin hub."),
    ("Departed Origin Hub", "The vehicle has left the origin warehouse.",
     "Track the LR number for the next update.", "The shipment moves in transit to the next hub."),
    ("In Transit", "The shipment is moving between hubs (see SS-002).",
     "Wait for the next update. In-transit status refreshes every 30 minutes.", "The shipment reaches a transit hub or the destination hub."),
    ("Arrived at Transit Hub", "The shipment reached an intermediate hub on its route.",
     "No action is needed.", "It departs for the next leg of the route."),
    ("Arrived at Destination Hub", "The shipment reached the hub that serves the delivery city.",
     "Check whether a delivery is already scheduled.", "The goods are unloaded and sorted for delivery."),
    ("Unloaded and Sorted", "The cartons are unloaded and sorted by delivery route.",
     "No action is needed.", "The shipment is assigned to a Delivery Executive."),
    ("Out for Delivery", "A Delivery Executive is taking the shipment to the consignee today (see SS-003).",
     "Make sure the receiver is available to sign.", "A delivery attempt is made within delivery hours."),
    ("Delivery Attempted", "A delivery was tried but could not be completed.",
     "Contact the Logistics Coordinator if the address or time is wrong.", "Another attempt is made, up to three attempts in total."),
    ("Delivered", "The consignee received the goods and the POD is captured (see SS-005).",
     "Check the goods and write any damage or shortage on the POD.", "Nothing further. The shipment is complete."),
    ("POD Uploaded", "The signed proof of delivery has been uploaded to the system.",
     "Download the POD from the client portal if you need a copy.", "The shipment record is closed."),
    ("Consignee Unavailable", "Nobody was present at the delivery address during the attempt.",
     "Tell the Logistics Coordinator the best time for the next attempt.", "The next attempt is scheduled within delivery hours."),
    ("Address Not Found", "The delivery address could not be located.",
     "Send a corrected address or a nearby landmark to the Logistics Coordinator.", "The address is verified before the next attempt."),
    ("Refused by Consignee", "The consignee refused the delivery.",
     "Contact the Logistics Coordinator to agree the next step with the sender.", "The shipment is re-attempted or returned as agreed."),
    ("Rescheduled", "The delivery date was moved at the request of the sender or receiver.",
     "Confirm the new date with your Logistics Coordinator.", "Delivery happens on the new date."),
    ("Held for Documents", "Required documents are missing, so the shipment is on hold (see SS-004).",
     "Send the missing invoice or e-way bill to the Logistics Coordinator.", "The hold is released once the documents are attached."),
    ("Held for Weather", "Weather is delaying road movement. The reason code is shown on the tracking page.",
     "Expect a delay. No action is needed.", "Movement resumes when conditions improve."),
    ("Held for Road Block", "A road closure or traffic restriction is delaying the vehicle.",
     "No action is needed. Monitor the status.", "The vehicle is re-routed or resumes its route."),
    ("Vehicle Breakdown", "The vehicle developed a fault on the way.",
     "Expect a delay. The Logistics Coordinator may arrange a replacement vehicle.", "The goods transfer to a replacement vehicle."),
    ("Capacity Shortage", "The carrier does not have enough capacity to move the shipment on the planned date.",
     "Ask the Logistics Coordinator for the revised date.", "A different vehicle is assigned."),
    ("Damage Reported in Transit", "Damage was noted at a hub or during transit.",
     "Keep the packaging and take photos at delivery.", "A damage claim is opened under PO-001."),
    ("Shortage Reported", "A count at a hub shows fewer cartons than the packing list.",
     "Compare the invoice and packing list with the cartons you received.", "The discrepancy is investigated."),
    ("Hold Released", "The reason for the hold has been cleared.",
     "No action is needed.", "The shipment resumes its route."),
    ("Re-routed", "The shipment is sent by a different route to avoid a delay.",
     "Expect a changed transit time.", "The shipment continues to the destination."),
    ("Return Initiated", "The shipment has been marked for return to the origin (see DP-001).",
     "Confirm with the sender what to do with the goods.", "The return leg is dispatched."),
    ("Returned to Origin", "The shipment has reached the origin hub after a return.",
     "Arrange the next step with the sender.", "The goods are received back into stock."),
    ("Cancelled", "The booking was cancelled before the goods were picked up.",
     "Confirm the cancellation in writing if you need a record.", "The LR is closed."),
    ("Address Change Requested", "A change of delivery address was requested (see FAQ-002).",
     "Confirm the new address and any re-routing fee.", "The change is applied if the shipment can still be re-routed."),
    ("Priority Flag Added", "The shipment was marked priority at booking or later (see CO-002).",
     "Expect daily status checks from the Logistics Coordinator.", "Escalation applies if there is no resolution within 4 hours."),
    ("Documents Verified", "The required documents were checked and accepted.",
     "No action is needed.", "Dispatch continues."),
    ("Returned Delivered", "The returned shipment reached the sender.",
     "Confirm receipt with the Logistics Coordinator.", "The shipment record is closed."),
]

# Glossary: (term, definition). Terms already in the original TM-* rows are not repeated.
GLOSSARY = [
    ("Bill of lading (B/L)", "A sea freight document issued by the ocean carrier. It is evidence that cargo was received and of the terms of the shipping contract."),
    ("Airway bill (AWB)", "The air cargo document issued by the airline or forwarder for a consignment. Unlike a bill of lading, it is not a title document."),
    ("Bin", "A numbered storage location in the warehouse, recorded in the WMS."),
    ("Bulk cargo", "Goods shipped loose rather than in packages, such as grain or coal."),
    ("Carrier", "The company that physically moves the goods, such as a road transporter, airline or shipping line."),
    ("Carton", "A corrugated cardboard box used as the basic outer pack for a shipment."),
    ("Chargeable weight", "The higher of actual weight and volumetric weight, used to price a shipment."),
    ("Consignee", "The person or company who receives the goods."),
    ("Consignor", "The person or company who sends the goods. Also called the shipper."),
    ("Container", "A standard steel box used for sea and rail freight, usually 20 or 40 feet long."),
    ("Cross-docking", "Moving goods straight from inbound to outbound with little or no storage in between."),
    ("Customs broker", "A licensed agent who files customs declarations for an importer or exporter."),
    ("Cycle count", "A partial stock count done on a rolling schedule, instead of one full stock take."),
    ("Dead stock", "Inventory that has not moved for a long time and is unlikely to sell."),
    ("Demurrage", "A charge for leaving a container at a port or terminal beyond the free time."),
    ("Detention", "A charge for keeping a container outside the terminal beyond the free time."),
    ("Dimensional weight", "Another name for volumetric weight, calculated from the length, width and height of a shipment."),
    ("Dispatch", "Sending a shipment out of the warehouse together with its documents."),
    ("Dunnage", "Packing material, such as wood or inflatable bags, that stops cargo moving inside a container or vehicle."),
    ("Incoterms", "Standard international trade terms that set who pays for transport and who carries the risk at each stage of a sale."),
    ("EXW (Ex Works)", "The buyer collects the goods from the seller's premises and takes on most of the cost and risk."),
    ("FOB (Free on Board)", "The seller delivers the goods on board the vessel at the port of shipment."),
    ("CIF (Cost, Insurance and Freight)", "The seller pays the cost, insurance and freight to the named destination port."),
    ("DAP (Delivered at Place)", "The seller delivers the goods ready for unloading at the named place. The buyer handles import clearance."),
    ("DDP (Delivered Duty Paid)", "The seller delivers the goods cleared for import, with all duties paid."),
    ("Forwarder", "A company that arranges transport and paperwork for shipments, often using several carriers."),
    ("Freight", "The charge for moving goods, or the goods being moved, depending on the context."),
    ("Goods receipt note (GRN)", "A record made at receiving that confirms goods arrived and were checked."),
    ("GST (Goods and Services Tax)", "India's indirect tax on the supply of goods and services."),
    ("GSTIN", "The 15-character GST identification number of a registered business."),
    ("HSN code", "A standard code that classifies goods for GST purposes."),
    ("HS code", "The Harmonized System code used internationally to classify goods for customs duty."),
    ("Hub", "A consolidation or distribution point where shipments are sorted and transferred."),
    ("ICD (Inland Container Depot)", "A container terminal located inland, where containers are stored, cleared and transferred."),
    ("Inbound", "Goods coming into a warehouse or location."),
    ("Inventory", "The stock of goods a business holds."),
    ("Last mile", "The final leg of delivery, from a local hub to the consignee."),
    ("Load securing", "Methods such as straps, blocking and bracing that stop cargo moving during transit."),
    ("Lot number", "A code that groups items made or received together, used for traceability."),
    ("Manifest", "A list of all the shipments or items on one vehicle, flight or vessel."),
    ("Mode of transport", "The method used to move goods, such as road, rail, air, sea or a combination."),
    ("Outbound", "Goods leaving a warehouse or location."),
    ("Pallet", "A flat platform, usually wood or plastic, used to move and stack goods with a forklift."),
    ("Pick list", "The list of items and bin locations a picker follows to gather an order."),
    ("Put-away", "Moving received goods into their storage bins and recording the location."),
    ("Quarantine", "A separate area for goods on hold, such as damaged or unverified stock."),
    ("Reason code", "A short code that explains why a shipment has an exception, such as a hold or delay."),
    ("Reverse logistics", "Moving goods back from the consignee for return, repair or disposal."),
    ("Route", "The planned sequence of hubs and legs that a shipment follows."),
    ("Safety stock", "Extra stock kept to cover unexpected demand or late supply."),
    ("SKU (stock keeping unit)", "A unique code for each distinct product variant held in stock."),
    ("Shrinkage", "Stock lost from inventory through damage, theft or counting errors."),
    ("Slotting", "Assigning products to storage locations, usually based on how fast they move."),
    ("Stock take", "A full physical count of all inventory in a warehouse."),
    ("Tare weight", "The weight of an empty container, vehicle or packaging."),
    ("Gross weight", "The total weight of the goods plus their packaging."),
    ("Net weight", "The weight of the goods alone, without packaging."),
    ("Transshipment", "Moving cargo from one vehicle or vessel to another on the way to its destination."),
    ("Unit load", "Goods combined into one handling unit, such as a palletised load or a shrink-wrapped stack."),
    ("Volumetric weight", "A weight calculated from the size of a shipment. It applies when a shipment is bulky but light."),
    ("Warehouse Management System (WMS)", "Software that tracks stock locations, movements and orders inside a warehouse."),
    ("Zone", "A defined area of the warehouse, such as fast-moving stock or hazardous storage."),
    ("Cold chain", "A chain of temperature-controlled storage and transport that keeps goods within the required range."),
    ("Temperature log", "A record of temperature readings for goods in storage or in transit."),
    ("Hazmat", "Short for hazardous materials: goods that can pose a risk to people, property or the environment."),
    ("UN number", "A four-digit code that identifies a dangerous good for transport."),
    ("Fragile mark", "A label that tells handlers the carton contains breakable goods."),
    ("Pilferage", "Theft of small quantities of goods from a shipment or warehouse."),
    ("Customs clearance", "The process by which customs releases goods after declarations are filed and duties are settled."),
    ("Lead time", "The time between placing an order and receiving the goods."),
    ("Expiry date", "The date after which a product should no longer be used or sold."),
    ("Shelf life", "How long a product stays fit for use or sale."),
    ("Serial number", "A unique number given to an individual item, used for tracking and warranty."),
    ("Batch", "A group of items produced together under the same conditions."),
    ("Backorder", "An order that cannot be filled from current stock and waits for replenishment."),
    ("Consolidation", "Combining several small shipments into one larger load to reduce cost."),
]

# Warehouse operations: (topic, content).
WAREHOUSE = [
    ("Receiving dock check", "Every inbound vehicle is checked at the dock against the ASN before unloading. Seals are verified and noted on the receiving record."),
    ("Put-away after receiving", "After receiving, goods are moved to their bin, and the bin location is scanned into the WMS."),
    ("Daily cycle counting", "A small set of bins is counted every day on a rotating schedule, so differences are found early without stopping operations."),
    ("Monthly stock reconciliation", "System stock is compared with physical counts each month. Differences are investigated before any adjustment is posted."),
    ("Quarantine handling", "Damaged or unverified goods go to a separate quarantine area and are not picked until the Warehouse Manager releases them."),
    ("Returns receiving", "Returned goods are inspected and recorded with their return reason. They are then restocked, repaired or moved to quarantine."),
    ("Cross-docking at the dock", "Goods that already have a dispatch order move from the dock straight to the outbound bay, with little or no storage."),
    ("Loading sequence", "Cartons are loaded in reverse delivery order, so the first delivery is accessible when the vehicle is opened."),
    ("Load securing before departure", "Cargo is strapped or blocked before the vehicle leaves, and the securing is checked at the gate."),
    ("Pallet build standard", "Pallets are built square, with heavy items at the bottom and the stack kept within the height and weight limits of the goods."),
    ("Stacking limits", "The printed stacking limit on each carton is respected. Cartons are never stacked on top of fragile goods."),
    ("Forklift safety", "Only trained operators use forklifts. Pedestrians stay out of marked lanes, and loads are kept low while travelling."),
    ("Personal protective equipment", "Staff wear safety shoes and gloves on the dock, and high-visibility vests in the yard."),
    ("Fire exits and extinguishers", "Fire exits and extinguisher points are kept clear at all times. Blocked exits are reported to the Warehouse Manager at once."),
    ("Housekeeping", "Aisles are cleared at the end of each shift, and spilled liquids are cleaned up immediately to prevent slips."),
    ("Pest control", "Regular inspection and treatment reduce rodent and insect risk. Records are kept, especially for food and grain stock."),
    ("Cold room temperature logging", "Temperatures in the cold area are logged at set intervals. Any reading outside the required range is escalated at once."),
    ("Dock door scheduling", "Inbound and outbound vehicles are assigned dock doors so that loading and unloading do not overlap."),
    ("Gate check-in", "Every vehicle is logged at the gate with its number and driver details. Gate passes are issued where needed."),
    ("Vehicle inspection before loading", "The loading bay checks the vehicle for cleanliness, damage and fitness to carry the goods before loading starts."),
    ("Seal verification", "Seal numbers are checked against the documents at loading and at receiving. A broken or mismatched seal is reported at once."),
    ("Container stuffing record", "Each container load is recorded with its seal number, weight and carton count, and photographed where required."),
    ("Labelling at packing", "Each carton gets a label with the LR number, carton number and destination before it leaves the packing station."),
    ("Barcode scanning at pick and dispatch", "Every carton and pallet is scanned at pick, pack and dispatch, so the system matches what was actually moved."),
    ("Serial number capture", "Serialised products are scanned at receiving and dispatch, so each unit can be traced."),
    ("Batch capture at receiving", "Batch and expiry details are captured at receiving and linked to each bin, so that recalls can be traced."),
    ("Near-expiry monitoring", "A weekly report lists stock close to expiry, so it can be dispatched or flagged before it becomes dead stock."),
    ("Dead stock review", "Items that have not moved for a long time are reviewed with the client to decide on return, discount or disposal."),
    ("Safety stock settings", "Each client's safety stock level is set in the WMS. The Warehouse Manager is alerted when stock falls below it."),
    ("Replenishment from reserve", "Forward pick bins are topped up from reserve storage before they run out, so pickers are not held up."),
    ("Slotting by movement speed", "Fast-moving products are placed near the dispatch bays and slow movers further back, to reduce travel time."),
    ("Order consolidation", "Orders for the same consignee or route are combined where possible, to reduce the number of vehicles and cartons."),
    ("Packing material control", "Cartons, tape and dunnage are issued against orders, and stock is counted monthly to control wastage."),
    ("Damage recording", "Damage found during handling is photographed and recorded in the WMS with a damage code. The Warehouse Manager is informed."),
    ("Weighing and dimension capture", "Each carton's weight and dimensions are recorded at packing. This supports billing and the chargeable weight calculation."),
    ("Shrinkage investigation", "Unexplained shortages are investigated by comparing scan logs, CCTV footage where available, and count records."),
    ("Shift handover", "Each shift ends with a handover note covering open exceptions, pending dispatches and any hazards."),
    ("Incident reporting", "Accidents, near misses and spills are reported on the same day, with the time, location and people involved."),
    ("Access control", "Only authorised staff and visitors enter the storage area. Visitors sign in and wear visitor badges."),
    ("Hazmat segregation", "Hazardous goods are stored only in Zone H, and incompatible materials are kept apart as set in the storage plan."),
    ("Spill kits", "Spill kits are placed near chemical and liquid storage, and staff are trained to use them."),
    ("Monsoon preparation", "Before the monsoon, roofs, drains and low-lying areas are checked, and stock is moved off the floor where water can reach it."),
    ("Festival season planning", "Peak periods before festivals are planned in advance, with extra staff, dock slots and safety stock."),
    ("Dispatch confirmation", "A dispatch is confirmed only after the documents, weights and carton counts match the order, and the status is updated."),
    ("Pick accuracy checks", "Random picks are re-checked each day, and any pick error is traced to the picker and the bin label."),
    ("Two-person check for high-value goods", "High-value consignments are counted and sealed by two people, and the sealing is recorded."),
]

# Claims: each condition is combined with each goods family.
CONDITIONS = [
    ("outer carton crushed", "Note the crushed carton on the POD at the door, photograph all sides, and keep the carton until the claim is closed."),
    ("carton wet or water-stained", "Photograph the stain and the inner packing, and check whether the contents are affected before signing for them."),
    ("broken seal or tampering", "Do not accept the goods without noting the seal condition on the POD, and photograph the seal and the carton."),
    ("missing item", "Compare the carton count with the packing list and write the number of missing items on the POD."),
    ("short quantity", "Count each unit against the invoice and record the quantity actually received."),
    ("wrong item delivered", "Record the wrong item by model or part number, and keep its original packaging."),
    ("broken or cracked item", "Photograph the broken item and its packaging, and note the damage on the POD."),
    ("item not working", "Keep the item in its original packaging and note its serial number. Do not attempt repairs before the claim is recorded."),
    ("leakage", "Photograph the leaking area, keep the container, and note the leakage on the POD."),
    ("near expiry or expired on arrival", "Record the batch and expiry dates, and note the expiry issue on the POD with photos."),
    ("damaged pallet", "Note the pallet condition, photograph the pallet and the load, and check the stack for shifted cartons."),
]
GOODS = [
    ("electronics", "Keep the serial number and original packaging with the claim."),
    ("garments", "Keep the piece count and the packing list with the claim."),
    ("ceramic tiles", "Keep the box labels and batch number with the claim."),
    ("pharmaceutical products", "Keep the batch number, expiry date and batch certificate with the claim."),
    ("food products", "Keep the batch number, expiry date and a photo of the label with the claim."),
    ("auto parts", "Keep the part numbers and the packing list with the claim."),
    ("packaged FMCG goods", "Keep the SKU and batch details with the claim."),
]

# Policies: (policy, content). Terms that depend on the client agreement point to it.
POLICIES = [
    ("Booking cancellation", "To cancel a booking, contact the Logistics Coordinator in writing. Cancellation terms are set out in the client agreement. A booking that has already been picked up is handled as a return or re-routing request."),
    ("Pickup rescheduling", "The sender can reschedule a pickup through the Logistics Coordinator. The new date is confirmed before the carrier is reassigned."),
    ("Failed pickup", "If the sender is not ready at the pickup time, the attempt is logged as Pickup Attempted and a new pickup is scheduled."),
    ("Weight and volume disputes", "If the weighed weight differs from the booked weight, the Logistics Coordinator reviews the weighment slip and the packing list before the bill is finalised."),
    ("Invoice queries", "Billing queries must be raised in writing with the invoice number. Disputes not resolved at Level 1 move to the Operations Manager (see PO-004)."),
    ("Payment terms", "Payment terms are set in the client agreement. Check the agreement, or contact your account manager, for the terms that apply to you."),
    ("Extended cover at booking", "Extended insurance cover must be selected at booking. Goods without extended cover are protected only up to the carrier liability limit (see PO-001)."),
    ("Prohibited and restricted goods", "Goods that are illegal to transport, or that the carrier does not accept, cannot be booked. Ask the Logistics Coordinator before booking any unusual item."),
    ("Hazardous goods rules", "Hazardous goods move only with a carrier holding a valid hazmat certificate, and they are stored only in Zone H (see SP-002 and WO-002)."),
    ("Customs and declarations", "The client is responsible for the accuracy of invoices, HS codes and declared values on export and import documents."),
    ("Force majeure", "Delays caused by events outside FleetHarbor's control, such as natural disasters, strikes or government action, are not treated as service failures. The status and reason code are updated as events happen."),
    ("Holiday schedule", "Deliveries run Monday to Saturday between 9:00 AM and 7:00 PM. Public holidays can change the schedule, and the Logistics Coordinator confirms revised dates."),
    ("Complaint handling", "Complaints start with the Logistics Coordinator for the lane. Unresolved complaints move to the Operations Manager and then to the Head of Operations (see PO-004)."),
    ("Consignee refusal", "If the consignee refuses delivery, the shipment is logged as a Failed Attempt with the refusal reason, and the sender is contacted for the next step."),
    ("Data access requests", "Clients can request records of their own shipments through the Logistics Coordinator. Consignee data is handled as described in the data and privacy policy (see PO-003)."),
    ("Document retention", "Shipping documents are kept in the system for the period set in the client agreement and as required by applicable law."),
    ("Packaging responsibility", "The client is responsible for packaging that suits the goods and the route. FleetHarbor may refuse packaging that appears unsafe and will record the reason."),
    ("Client portal access", "Each client user has a named login for the client portal. Access should be shared only with users the client has authorised."),
    ("Contact changes", "The client must tell FleetHarbor in writing when a pickup or consignee contact changes, so that the updated details are used for dispatch and delivery."),
    ("Escalation of priority shipments", "A priority shipment moves to the next escalation level if it has no resolution within 4 hours (see PO-004 and CO-002)."),
    ("Support hours", "Support is provided through the Logistics Coordinator during working hours. Priority issues follow the escalation matrix."),
]

# Customer questions in everyday language. Each answer follows the original rows.
FAQS = [
    ("How do I know my order has shipped?", "Check the tracking page with your order ID or LR number. The status changes to In Transit once the carrier has picked up the shipment (see SS-002)."),
    ("Can I ask for a different delivery time?", "Deliveries run from 9:00 AM to 7:00 PM, Monday to Saturday. Ask the Logistics Coordinator for your lane to request a time within these hours. Any delivery outside them needs written approval from the Operations Manager and the client."),
    ("What is an LR number?", "The LR number is the lorry receipt number generated at booking. It is shared with the carrier, so use it to track the shipment after booking (see TM-001)."),
    ("Why does my order show On Hold?", "A hold means an exception was logged with a reason code, such as missing documents, weather or capacity limits. The order is not cancelled, and the reason code is shown on the tracking page."),
    ("Can I change my order after it is dispatched?", "After dispatch, changes must be requested through the carrier, and a re-routing fee may apply. Ask the Logistics Coordinator for your lane as soon as possible."),
    ("How many delivery attempts will be made?", "Up to three delivery attempts are made. After the third failed attempt, the shipment returns to the origin hub (see DP-001)."),
    ("Do I need to sign for my delivery?", "Proof of delivery needs the receiver's name, a signature or OTP confirmation, and a timestamp (see DP-002)."),
    ("Can I send goods without an invoice?", "No. Dispatch is blocked in the system until the mandatory documents, including the invoice and packing list, are attached (see SP-003)."),
    ("Do you deliver on Sundays?", "Standard deliveries run Monday to Saturday. Any Sunday or out-of-hours delivery needs written approval from the Operations Manager and the client (see DP-003)."),
    ("Why was my shipment returned?", "A shipment is returned after three failed delivery attempts, or when a return is agreed. Its status then changes to Returned (see SS-005)."),
    ("How long do I have to return goods?", "Returns are accepted within 10 days of delivery for unused goods in their original packaging (see PO-002)."),
    ("Who pays for return freight?", "Return freight is charged to the client unless the return results from a FleetHarbor error (see PO-002)."),
    ("How much is my shipment insured for?", "Carrier liability is limited to the declared value of the goods, unless extended cover was bought at booking (see PO-001)."),
    ("Is my contact information shared with the carrier?", "Consignee details are used only for delivery. They are removed from active systems 90 days after proof of delivery and are not shared with third parties (see PO-003)."),
    ("Why is my tracking not updating?", "In-transit shipments refresh every 30 minutes. If the status has not changed in 24 hours, contact the Logistics Coordinator for your lane (see FAQ-001 and OT-001)."),
    ("What is the difference between an order ID and an LR number?", "Order IDs begin with ORD-. LR numbers begin with LR- and are shared with the carrier, so use the LR number to track after booking (see OT-002)."),
    ("How long does delivery take?", "Standard windows are 2 to 4 business days for intra-state shipments and 4 to 7 business days for inter-state shipments (see CO-002)."),
    ("How do I mark a shipment as priority?", "Priority shipments are flagged at booking. They receive daily status checks from the Logistics Coordinator (see CO-002)."),
    ("Who do I contact if my issue is not resolved?", "Start with the Logistics Coordinator (Level 1). If the issue is still open, it goes to the Operations Manager (Level 2), then to the Head of Operations (Level 3). A priority shipment moves up after 4 hours without resolution (see PO-004)."),
    ("Do you handle hazardous goods?", "Yes, but hazardous goods move only with a carrier that holds a valid hazmat certificate, and they are stored only in Zone H (see SP-002 and WO-002)."),
    ("Can you store my goods in your warehouse?", "FleetHarbor offers warehousing from its Ahmedabad, Vadodara and Rajkot warehouses (see CO-001). Contact your account manager to arrange storage."),
    ("How are goods picked from the warehouse?", "Perishable goods are picked FEFO, and all other goods are picked FIFO (see WO-003)."),
    ("What does Failed Attempt mean on my tracking?", "Failed Attempt means a delivery was tried but not completed. Each attempt is recorded with a reason code (see DP-001 and SS-005)."),
    ("What happens if I refuse a delivery?", "The refusal is logged as a Failed Attempt with its reason, and the sender is contacted for the next step."),
    ("How do I report missing cartons?", "Compare the carton count with the packing list, note the shortage on the POD at delivery, and raise a claim within 7 days with photos and the invoice (see PO-001)."),
    ("Is my order confirmed as soon as I place it?", "An order moves through Order Created and then Order Confirmed. The booking is made within 2 hours of confirmation (see LW-001 and SP-001)."),
    ("How do I track a shipment on the portal?", "Log in to the client portal and enter your order ID or LR number on the tracking page. You can also call support to speak to a team member (see OT-001)."),
    ("What if I cannot receive the goods at the delivery address?", "Tell the Logistics Coordinator the best time for the next attempt. Attempts are made only within delivery hours (see DP-003)."),
    ("What stages does an order go through?", "Every order moves through six stages: Order Created, Order Confirmed, Picked, Packed, Dispatched and Delivered (see LW-001)."),
    ("Does an exception cancel my order?", "No. An exception is logged as a hold with a reason code and does not cancel the order (see LW-001)."),
    ("What should I do if my tracking shows Delayed?", "Check the reason code on the tracking page. Weather, missing documents and capacity limits are the usual reasons. Contact the Logistics Coordinator if there is no update within 24 hours (see SS-004)."),
    ("Who signs the POD for a delivery?", "The receiver signs, or confirms by OTP, and the Delivery Executive records the receiver's name and a timestamp (see DP-002)."),
]


# ---------------------------------------------------------------------------
# Row generation
# ---------------------------------------------------------------------------

ROWS = []
_COUNTERS = Counter()


def emit(prefix, category, title, content, tags):
    _COUNTERS[prefix] += 1
    ROWS.append({
        "doc_id": f"{prefix}-{_COUNTERS[prefix]:04d}",
        "category": category,
        "section_title": title,
        "content": content,
        "tags": tags,
        "last_updated": LAST_UPDATED,
    })


def build_lanes():
    for hub in HUBS:
        for dest, state in DESTINATIONS:
            if dest == hub:
                continue
            kind = "intra" if state == "Gujarat" else "inter"
            movement = ("an intra-state movement within Gujarat" if kind == "intra"
                        else f"an inter-state movement from Gujarat to {state}")
            short = "intra-state" if kind == "intra" else "inter-state"
            window = WINDOW[kind]
            lane = f"{hub} to {dest}"
            base = f"lane;{hub.lower()};{dest.lower()};{short}"

            emit("LN", "lane_guide", f"{lane}: delivery window",
                 f"Shipments from {hub} to {dest} ({state}) are {movement}. The standard delivery window is {window} business days, as set out in the service levels. Priority shipments on this lane are flagged at booking and get daily status checks from the Logistics Coordinator.",
                 f"{base};delivery time;sla;priority")
            emit("LN", "lane_guide", f"{lane}: booking and dispatch cutoff",
                 f"A Logistics Coordinator books each {hub} to {dest} order within 2 hours of confirmation. Orders confirmed by 1:00 PM are dispatched the same day from {hub}, and later orders are dispatched on the next working day.",
                 f"{base};booking;cutoff;dispatch")
            docs_note = ("Because this movement is inter-state, the invoice must show the correct consignee state for GST purposes."
                         if kind == "inter" else
                         "Because this movement stays within Gujarat, the consignee address on the invoice must match the delivery address.")
            emit("LN", "lane_guide", f"{lane}: documents needed",
                 f"A {hub} to {dest} dispatch needs a commercial invoice, a packing list and the LR number generated at booking. Consignments valued above INR 50,000 also need an e-way bill under GST rules. {docs_note} Dispatch stays blocked until the mandatory documents are attached.",
                 f"{base};documents;e-way bill;GST")
            emit("LN", "lane_guide", f"{lane}: delivery and proof of delivery",
                 f"Shipments from {hub} to {dest} are delivered in {dest} between 9:00 AM and 7:00 PM, Monday to Saturday. Up to three delivery attempts are made, and each failed attempt is logged with a reason code. The proof of delivery must show the receiver's name, a signature or OTP confirmation and a timestamp.",
                 f"{base};delivery hours;POD;attempts")
            emit("LN", "lane_guide", f"{lane}: delays and escalation",
                 f"If a {hub} to {dest} shipment is delayed or on hold, the tracking page shows a reason code such as weather, missing documents or capacity limits. A priority shipment moves to the next escalation level if it has no resolution within 4 hours.",
                 f"{base};delay;hold;escalation")

            for label, handling, evidence in LANE_FAMILIES:
                emit("LC", "lane_commodity", f"Sending {label} from {hub} to {dest}",
                     f"{handling} This {hub} to {dest} lane is {short}, so the standard delivery window is {window} business days from dispatch. {evidence}",
                     f"{base};commodity;{label.replace(' ', '-')}")


def build_commodities():
    for name, pack, storage, label, docs, risk in PROFILES:
        n = name.lower()
        slug = n.replace(" ", "-")
        values = {"n": n, "pack": pack, "storage": storage, "label": label, "docs": docs, "risk": risk}
        for key, (title_t, content_t) in zip(ASPECT_KEYS, ASPECTS):
            emit("CM", "commodity_handling", title_t.format(**values), content_t.format(**values),
                 f"commodity;{key};{slug}")


def build_documents():
    for name, meaning, when, check in DOCUMENTS:
        tag = f"document;{name.lower()}"
        emit("DC", "document_guide", f"{name}: what it is",
             f"{meaning} The document travels with the consignment file, so it is kept with the invoice and packing list until the shipment is delivered.", tag)
        emit("DC", "document_guide", f"{name}: when it is required",
             f"{when} If a required copy is missing, tell the Logistics Coordinator before dispatch so the shipment is not put on hold (see SS-004).", tag)
        emit("DC", "document_guide", f"{name}: checks before dispatch",
             f"{check} Record any mismatch in the booking notes and inform the Logistics Coordinator before the vehicle leaves.", tag)


def build_events():
    for name, meaning, action, next_step in EVENTS:
        emit("EV", "tracking_events", f"Tracking event: {name}",
             f"{meaning} This event is shown on the tracking page for the shipment.", "tracking;event;status")
        emit("EV", "tracking_events", f"{name}: what to do",
             f"{meaning} What to do: {action}", "tracking;event;action")
        emit("EV", "tracking_events", f"{name}: what happens next",
             f"{meaning} What happens next: {next_step}", "tracking;event;next step")


def build_glossary():
    for term, definition in GLOSSARY:
        emit("GL", "glossary", term, definition, "glossary;term")


def build_warehouse():
    for topic, content in WAREHOUSE:
        emit("WH", "warehouse_operations", topic, content, "warehouse;operations")


def build_claims():
    for condition, guidance in CONDITIONS:
        for goods, evidence in GOODS:
            emit("CL", "claims_guidance", f"Claim for {condition} on {goods}",
                 f"{guidance} For {goods}: {evidence} Claims must be filed within 7 days of delivery with photos and the invoice (see PO-001 and FAQ-003). Carrier liability is limited to the declared value unless extended cover was bought at booking.",
                 f"claim;damage;{goods}")


def build_policies():
    for title, content in POLICIES:
        emit("PL", "policies", title, content, f"policy;{title.lower()}")


def build_faqs():
    for question, answer in FAQS:
        emit("FQ", "faq", question, answer, "faq;customer question")


# ---------------------------------------------------------------------------
# Checks and output
# ---------------------------------------------------------------------------

def load_original():
    with open(ORIGINAL, encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def validate(all_rows, original_count):
    problems = []
    for name in ("doc_id", "section_title", "content"):
        counts = Counter(r[name] for r in all_rows)
        dups = [value for value, count in counts.items() if count > 1]
        if dups:
            problems.append(f"duplicate {name}: {dups[:5]}")
    for r in all_rows:
        for field in FIELDS:
            if not (r.get(field) or "").strip():
                problems.append(f"{r.get('doc_id')}: empty {field}")
        for field in ("section_title", "content", "tags"):
            if not r[field].isascii():
                problems.append(f"{r['doc_id']}: non-ASCII character in {field}")
        generated = all_rows.index(r) >= original_count
        minimum = 30 if r["category"] == "glossary" else 60  # glossary definitions are naturally brief
        if generated and len(r["content"]) < minimum:
            problems.append(f"{r['doc_id']}: content too short ({len(r['content'])} chars)")
    if len(all_rows) < MIN_ROWS:
        problems.append(f"only {len(all_rows)} rows, need at least {MIN_ROWS}")
    if problems:
        raise SystemExit("Validation failed:\n" + "\n".join(problems[:50]))


def main():
    build_lanes()
    build_commodities()
    build_documents()
    build_events()
    build_glossary()
    build_warehouse()
    build_claims()
    build_policies()
    build_faqs()

    original = load_original()
    all_rows = original + ROWS
    validate(all_rows, len(original))

    with open(OUTPUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Wrote {len(all_rows)} rows to {OUTPUT}")
    for category, count in Counter(r["category"] for r in all_rows).most_common():
        print(f"  {category:22s} {count}")


if __name__ == "__main__":
    main()
