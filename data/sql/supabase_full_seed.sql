-- FleetHarbor Logistics PostgreSQL / Supabase Full Production Seed
-- Generated: 20 November 2026

-- 1. Create Shipments Table
CREATE TABLE IF NOT EXISTS public.shipments (
    shipment_id VARCHAR(32) PRIMARY KEY,
    origin VARCHAR(128) NOT NULL,
    destination VARCHAR(128) NOT NULL,
    status VARCHAR(64) NOT NULL,
    current_location VARCHAR(128),
    route TEXT,
    estimated_delivery DATE,
    delay_reason TEXT,
    customs_status VARCHAR(128),
    last_updated TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_shipments_status ON public.shipments(status);
CREATE INDEX IF NOT EXISTS idx_shipments_origin ON public.shipments(origin);
CREATE INDEX IF NOT EXISTS idx_shipments_destination ON public.shipments(destination);

-- 2. Seed Shipments Data
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10001', 'Mumbai, India', 'London, UK', 'In Transit', 'Dubai Hub, UAE', 'Mumbai Hub -> Dubai Hub -> London Heathrow Hub', '2026-11-20', NULL, 'Not yet required', '2026-11-15 18:30')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10002', 'Chennai, India', 'Dubai, UAE', 'Delayed', 'Jebel Ali Port, UAE', 'Chennai Port -> Jebel Ali Port', '2026-11-19', 'Port congestion at Jebel Ali', 'Cleared', '2026-11-16 08:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10003', 'Delhi, India', 'New York, USA', 'On Hold - Customs', 'JFK Airport, USA', 'Delhi Hub -> Frankfurt Hub -> JFK Airport', '2026-11-22', 'Customs hold', 'Held - awaiting commercial invoice', '2026-11-15 12:10')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10004', 'Ahmedabad, India', 'Singapore', 'Delivered', 'Singapore', 'Ahmedabad Hub -> Singapore Hub', '2026-11-10', NULL, 'Cleared', '2026-11-10 14:45')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10005', 'Pune, India', 'Sydney, Australia', 'Out for Delivery', 'Sydney Local Depot', 'Pune Hub -> Singapore Hub -> Sydney Hub', '2026-11-16', NULL, 'Cleared', '2026-11-16 07:20')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10006', 'Kolkata, India', 'Tokyo, Japan', 'In Transit', 'Singapore Hub', 'Kolkata Hub -> Singapore Hub -> Tokyo Hub', '2026-11-25', NULL, 'Pending', '2026-11-17 09:15')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10007', 'Bangalore, India', 'Berlin, Germany', 'Delayed', 'Mumbai Hub, India', 'Bangalore Hub -> Mumbai Hub -> Frankfurt Hub -> Berlin Depot', '2026-11-28', 'Weather disruption at Mumbai airport', 'Not yet required', '2026-11-17 06:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10008', 'Hyderabad, India', 'Toronto, Canada', 'In Transit', 'London Heathrow Hub, UK', 'Hyderabad Hub -> Dubai Hub -> London Hub -> Toronto Pearson Hub', '2026-11-24', NULL, 'Cleared', '2026-11-16 22:45')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10009', 'Jaipur, India', 'Dubai, UAE', 'Delivered', 'Dubai, UAE', 'Jaipur Hub -> Mumbai Hub -> Dubai Hub', '2026-11-12', NULL, 'Cleared', '2026-11-12 11:30')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10010', 'Surat, India', 'Los Angeles, USA', 'On Hold - Customs', 'LAX Airport, USA', 'Surat Hub -> Singapore Hub -> LAX Airport', '2026-11-26', 'Customs hold', 'Held - missing packing list', '2026-11-17 03:50')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10011', 'Mumbai, India', 'London, UK', 'Delayed', 'Transit Hub near Mumbai', 'Mumbai Hub -> Dubai Hub -> London Heathrow Hub', '2026-11-25', 'Severe weather and typhoon diversion in Pacific corridor', 'Export clearance completed', '2026-11-14 12:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10012', 'Singapore', 'Amsterdam, Netherlands', 'In Transit', 'In Transit (Doha Hub)', 'Changi Cargo -> Doha Hub -> Amsterdam Schiphol', '2026-11-17', NULL, 'Export clearance completed', '2026-11-14 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10013', 'Hong Kong', 'Frankfurt, Germany', 'In Transit', 'In Transit (Dubai)', 'Hong Kong Air Cargo -> Dubai -> Frankfurt CargoCity', '2026-11-20', NULL, 'Export clearance completed', '2026-11-14 11:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10014', 'Chennai, India', 'Singapore', 'Delayed', 'Transit Hub near Chennai', 'Chennai Port -> Port of Singapore -> Jurong Logistics Hub', '2026-11-25', 'Highway transit disruption and road transport detour', 'Cleared', '2026-11-14 20:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10015', 'Johannesburg, South Africa', 'London, UK', 'In Transit', 'In Transit (Nairobi Hub)', 'O.R. Tambo Airport -> Nairobi Hub -> London Heathrow', '2026-11-21', NULL, 'Duty payment processing', '2026-11-14 14:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10016', 'Delhi, India', 'Chicago, USA', 'Delayed', 'Transit Hub near Delhi', 'Delhi Air Cargo -> London Heathrow -> Chicago O''Hare Hub', '2026-11-22', 'Port congestion and vessel berthing backlog', 'Export clearance completed', '2026-11-14 13:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10017', 'Shanghai, China', 'Los Angeles, USA', 'On Hold - Customs', 'Los Angeles International Customs Exam Station', 'Shanghai Port -> Long Beach Port -> LA Intermodal Depot', '2026-11-17', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 10:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10018', 'Singapore', 'Amsterdam, Netherlands', 'Delivered', 'Amsterdam, Netherlands Consignee Facility', 'Changi Cargo -> Doha Hub -> Amsterdam Schiphol', '2026-11-12', NULL, 'Cleared', '2026-11-13 18:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10019', 'Busan, South Korea', 'Vancouver, Canada', 'In Transit', 'In Transit (Pacific Route)', 'Busan Port -> Pacific Route -> Vancouver Port', '2026-11-17', NULL, 'Export clearance completed', '2026-11-14 14:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10020', 'Dubai, UAE', 'New York, USA', 'Delivered', 'New York, USA Consignee Facility', 'Dubai Logistics City -> Frankfurt Airport -> JFK Cargo Center', '2026-11-13', NULL, 'Cleared', '2026-11-13 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10021', 'Hong Kong', 'Frankfurt, Germany', 'In Transit', 'In Transit (Dubai)', 'Hong Kong Air Cargo -> Dubai -> Frankfurt CargoCity', '2026-11-19', NULL, 'Duty payment processing', '2026-11-14 13:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10022', 'Shenzhen, China', 'Paris, France', 'On Hold - Customs', 'Paris International Customs Exam Station', 'Shenzhen Yantian -> Colombo Port -> Le Havre -> Paris Hub', '2026-11-17', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 15:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10023', 'Chennai, India', 'Singapore', 'On Hold - Customs', 'Singapore International Customs Exam Station', 'Chennai Port -> Port of Singapore -> Jurong Logistics Hub', '2026-11-20', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 14:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10024', 'Shanghai, China', 'Los Angeles, USA', 'In Transit', 'In Transit (Long Beach Port)', 'Shanghai Port -> Long Beach Port -> LA Intermodal Depot', '2026-11-21', NULL, 'Duty payment processing', '2026-11-14 20:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10025', 'Doha, Qatar', 'Madrid, Spain', 'In Transit', 'In Transit (Rome Transit)', 'Doha Hamad Airport -> Rome Transit -> Madrid Barajas Hub', '2026-11-23', NULL, 'Duty payment processing', '2026-11-14 21:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10026', 'Singapore', 'Amsterdam, Netherlands', 'In Transit', 'In Transit (Doha Hub)', 'Changi Cargo -> Doha Hub -> Amsterdam Schiphol', '2026-11-20', NULL, 'Duty payment processing', '2026-11-14 12:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10027', 'Taipei, Taiwan', 'Munich, Germany', 'Delivered', 'Munich, Germany Consignee Facility', 'Taoyuan Airport -> Frankfurt Hub -> Munich Cargo Terminal', '2026-11-11', NULL, 'Cleared', '2026-11-12 20:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10028', 'Rotterdam, Netherlands', 'Sydney, Australia', 'Delivered', 'Sydney, Australia Consignee Facility', 'Rotterdam Port -> Suez Canal -> Singapore -> Sydney Mascot Depot', '2026-11-14', NULL, 'Cleared', '2026-11-13 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10029', 'Rotterdam, Netherlands', 'Sydney, Australia', 'Delivered', 'Sydney, Australia Consignee Facility', 'Rotterdam Port -> Suez Canal -> Singapore -> Sydney Mascot Depot', '2026-11-11', NULL, 'Cleared', '2026-11-13 17:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10030', 'Hong Kong', 'Frankfurt, Germany', 'Delivered', 'Frankfurt, Germany Consignee Facility', 'Hong Kong Air Cargo -> Dubai -> Frankfurt CargoCity', '2026-11-11', NULL, 'Cleared', '2026-11-12 15:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10031', 'Mumbai, India', 'London, UK', 'Delayed', 'Transit Hub near Mumbai', 'Mumbai Hub -> Dubai Hub -> London Heathrow Hub', '2026-11-27', 'Port congestion and vessel berthing backlog', 'Export clearance completed', '2026-11-14 14:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10032', 'Shenzhen, China', 'Paris, France', 'In Transit', 'In Transit (Colombo Port)', 'Shenzhen Yantian -> Colombo Port -> Le Havre -> Paris Hub', '2026-11-18', NULL, 'Export clearance completed', '2026-11-14 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10033', 'Mumbai, India', 'London, UK', 'Out for Delivery', 'London, UK Local Delivery Center', 'Mumbai Hub -> Dubai Hub -> London Heathrow Hub', '2026-11-15', NULL, 'Cleared', '2026-11-14 18:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10034', 'Singapore', 'Amsterdam, Netherlands', 'Out for Delivery', 'Amsterdam, Netherlands Local Delivery Center', 'Changi Cargo -> Doha Hub -> Amsterdam Schiphol', '2026-11-15', NULL, 'Cleared', '2026-11-14 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10035', 'Sao Paulo, Brazil', 'Miami, USA', 'Out for Delivery', 'Miami, USA Local Delivery Center', 'Santos Port -> Caribbean Route -> Port of Miami', '2026-11-15', NULL, 'Cleared', '2026-11-14 18:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10036', 'Antwerp, Belgium', 'Toronto, Canada', 'On Hold - Customs', 'Toronto International Customs Exam Station', 'Antwerp Port -> Halifax Port -> Toronto Logistics Terminal', '2026-11-21', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10037', 'Rotterdam, Netherlands', 'Sydney, Australia', 'In Transit', 'In Transit (Suez Canal)', 'Rotterdam Port -> Suez Canal -> Singapore -> Sydney Mascot Depot', '2026-11-16', NULL, 'Not yet required', '2026-11-14 14:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10038', 'Shenzhen, China', 'Paris, France', 'Delivered', 'Paris, France Consignee Facility', 'Shenzhen Yantian -> Colombo Port -> Le Havre -> Paris Hub', '2026-11-14', NULL, 'Cleared', '2026-11-12 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10039', 'Hamburg, Germany', 'Mumbai, India', 'In Transit', 'In Transit (Suez Transit)', 'Hamburg Port -> Suez Transit -> JNPT Mumbai', '2026-11-17', NULL, 'Duty payment processing', '2026-11-14 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10040', 'Doha, Qatar', 'Madrid, Spain', 'On Hold - Customs', 'Madrid International Customs Exam Station', 'Doha Hamad Airport -> Rome Transit -> Madrid Barajas Hub', '2026-11-21', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 18:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10041', 'Rotterdam, Netherlands', 'Sydney, Australia', 'Delayed', 'Transit Hub near Rotterdam', 'Rotterdam Port -> Suez Canal -> Singapore -> Sydney Mascot Depot', '2026-11-23', 'Highway transit disruption and road transport detour', 'Not yet required', '2026-11-14 06:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10042', 'Zurich, Switzerland', 'Boston, USA', 'Delivered', 'Boston, USA Consignee Facility', 'Zurich Airport -> Dublin Hub -> Boston Logan Freight', '2026-11-13', NULL, 'Cleared', '2026-11-13 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10043', 'Hong Kong', 'Frankfurt, Germany', 'Out for Delivery', 'Frankfurt, Germany Local Delivery Center', 'Hong Kong Air Cargo -> Dubai -> Frankfurt CargoCity', '2026-11-15', NULL, 'Cleared', '2026-11-14 18:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10044', 'Busan, South Korea', 'Vancouver, Canada', 'Delivered', 'Vancouver, Canada Consignee Facility', 'Busan Port -> Pacific Route -> Vancouver Port', '2026-11-11', NULL, 'Cleared', '2026-11-13 20:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10045', 'Hamburg, Germany', 'Mumbai, India', 'In Transit', 'In Transit (Suez Transit)', 'Hamburg Port -> Suez Transit -> JNPT Mumbai', '2026-11-19', NULL, 'Not yet required', '2026-11-14 14:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10046', 'Hamburg, Germany', 'Mumbai, India', 'In Transit', 'In Transit (Suez Transit)', 'Hamburg Port -> Suez Transit -> JNPT Mumbai', '2026-11-16', NULL, 'Duty payment processing', '2026-11-14 20:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10047', 'Shanghai, China', 'Los Angeles, USA', 'Out for Delivery', 'Los Angeles, USA Local Delivery Center', 'Shanghai Port -> Long Beach Port -> LA Intermodal Depot', '2026-11-15', NULL, 'Cleared', '2026-11-14 21:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10048', 'Shanghai, China', 'Los Angeles, USA', 'Delivered', 'Los Angeles, USA Consignee Facility', 'Shanghai Port -> Long Beach Port -> LA Intermodal Depot', '2026-11-12', NULL, 'Cleared', '2026-11-12 20:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10049', 'Johannesburg, South Africa', 'London, UK', 'In Transit', 'In Transit (Nairobi Hub)', 'O.R. Tambo Airport -> Nairobi Hub -> London Heathrow', '2026-11-23', NULL, 'Duty payment processing', '2026-11-14 20:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10050', 'Doha, Qatar', 'Madrid, Spain', 'On Hold - Customs', 'Madrid International Customs Exam Station', 'Doha Hamad Airport -> Rome Transit -> Madrid Barajas Hub', '2026-11-18', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10051', 'Frankfurt, Germany', 'Tokyo, Japan', 'Delayed', 'Transit Hub near Frankfurt', 'Frankfurt Airport -> Dubai Cargo Hub -> Tokyo Narita Hub', '2026-11-25', 'Partner airline mechanical inspection delay', 'Inspection required - Physical examination scheduled', '2026-11-14 08:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10052', 'Chennai, India', 'Singapore', 'Delayed', 'Transit Hub near Chennai', 'Chennai Port -> Port of Singapore -> Jurong Logistics Hub', '2026-11-19', 'Customs secondary inspection and valuation audit', 'Cleared', '2026-11-14 10:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10053', 'Shenzhen, China', 'Paris, France', 'On Hold - Customs', 'Paris International Customs Exam Station', 'Shenzhen Yantian -> Colombo Port -> Le Havre -> Paris Hub', '2026-11-17', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 15:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10054', 'Delhi, India', 'Chicago, USA', 'In Transit', 'In Transit (London Heathrow)', 'Delhi Air Cargo -> London Heathrow -> Chicago O''Hare Hub', '2026-11-18', NULL, 'Export clearance completed', '2026-11-14 17:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10055', 'Dubai, UAE', 'New York, USA', 'In Transit', 'In Transit (Frankfurt Airport)', 'Dubai Logistics City -> Frankfurt Airport -> JFK Cargo Center', '2026-11-17', NULL, 'Not yet required', '2026-11-14 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10056', 'Johannesburg, South Africa', 'London, UK', 'In Transit', 'In Transit (Nairobi Hub)', 'O.R. Tambo Airport -> Nairobi Hub -> London Heathrow', '2026-11-16', NULL, 'Duty payment processing', '2026-11-14 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10057', 'Hamburg, Germany', 'Mumbai, India', 'In Transit', 'In Transit (Suez Transit)', 'Hamburg Port -> Suez Transit -> JNPT Mumbai', '2026-11-23', NULL, 'Export clearance completed', '2026-11-14 20:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10058', 'Hong Kong', 'Frankfurt, Germany', 'Out for Delivery', 'Frankfurt, Germany Local Delivery Center', 'Hong Kong Air Cargo -> Dubai -> Frankfurt CargoCity', '2026-11-15', NULL, 'Cleared', '2026-11-14 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10059', 'Hong Kong', 'Frankfurt, Germany', 'In Transit', 'In Transit (Dubai)', 'Hong Kong Air Cargo -> Dubai -> Frankfurt CargoCity', '2026-11-20', NULL, 'Export clearance completed', '2026-11-14 11:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10060', 'Melbourne, Australia', 'Auckland, New Zealand', 'In Transit', 'In Transit (Tasman Sea Route)', 'Melbourne Port -> Tasman Sea Route -> Auckland Wharf', '2026-11-23', NULL, 'Duty payment processing', '2026-11-14 21:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10061', 'Delhi, India', 'Chicago, USA', 'In Transit', 'In Transit (London Heathrow)', 'Delhi Air Cargo -> London Heathrow -> Chicago O''Hare Hub', '2026-11-16', NULL, 'Not yet required', '2026-11-14 12:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10062', 'Shenzhen, China', 'Paris, France', 'In Transit', 'In Transit (Colombo Port)', 'Shenzhen Yantian -> Colombo Port -> Le Havre -> Paris Hub', '2026-11-23', NULL, 'Duty payment processing', '2026-11-14 15:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10063', 'Sao Paulo, Brazil', 'Miami, USA', 'In Transit', 'In Transit (Caribbean Route)', 'Santos Port -> Caribbean Route -> Port of Miami', '2026-11-17', NULL, 'Duty payment processing', '2026-11-14 10:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10064', 'Dubai, UAE', 'New York, USA', 'In Transit', 'In Transit (Frankfurt Airport)', 'Dubai Logistics City -> Frankfurt Airport -> JFK Cargo Center', '2026-11-19', NULL, 'Not yet required', '2026-11-14 17:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10065', 'Frankfurt, Germany', 'Tokyo, Japan', 'Out for Delivery', 'Tokyo, Japan Local Delivery Center', 'Frankfurt Airport -> Dubai Cargo Hub -> Tokyo Narita Hub', '2026-11-15', NULL, 'Cleared', '2026-11-14 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10066', 'Hamburg, Germany', 'Mumbai, India', 'Delivered', 'Mumbai, India Consignee Facility', 'Hamburg Port -> Suez Transit -> JNPT Mumbai', '2026-11-14', NULL, 'Cleared', '2026-11-13 17:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10067', 'Taipei, Taiwan', 'Munich, Germany', 'Delivered', 'Munich, Germany Consignee Facility', 'Taoyuan Airport -> Frankfurt Hub -> Munich Cargo Terminal', '2026-11-12', NULL, 'Cleared', '2026-11-12 20:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10068', 'Shenzhen, China', 'Paris, France', 'In Transit', 'In Transit (Colombo Port)', 'Shenzhen Yantian -> Colombo Port -> Le Havre -> Paris Hub', '2026-11-18', NULL, 'Export clearance completed', '2026-11-14 13:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10069', 'Antwerp, Belgium', 'Toronto, Canada', 'Delivered', 'Toronto, Canada Consignee Facility', 'Antwerp Port -> Halifax Port -> Toronto Logistics Terminal', '2026-11-14', NULL, 'Cleared', '2026-11-13 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10070', 'Zurich, Switzerland', 'Boston, USA', 'Out for Delivery', 'Boston, USA Local Delivery Center', 'Zurich Airport -> Dublin Hub -> Boston Logan Freight', '2026-11-15', NULL, 'Cleared', '2026-11-14 23:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10071', 'Shanghai, China', 'Los Angeles, USA', 'Delivered', 'Los Angeles, USA Consignee Facility', 'Shanghai Port -> Long Beach Port -> LA Intermodal Depot', '2026-11-12', NULL, 'Cleared', '2026-11-13 18:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10072', 'Shanghai, China', 'Los Angeles, USA', 'On Hold - Customs', 'Los Angeles International Customs Exam Station', 'Shanghai Port -> Long Beach Port -> LA Intermodal Depot', '2026-11-19', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 13:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10073', 'Dubai, UAE', 'New York, USA', 'Delivered', 'New York, USA Consignee Facility', 'Dubai Logistics City -> Frankfurt Airport -> JFK Cargo Center', '2026-11-12', NULL, 'Cleared', '2026-11-13 15:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10074', 'Antwerp, Belgium', 'Toronto, Canada', 'Out for Delivery', 'Toronto, Canada Local Delivery Center', 'Antwerp Port -> Halifax Port -> Toronto Logistics Terminal', '2026-11-15', NULL, 'Cleared', '2026-11-14 23:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10075', 'Rotterdam, Netherlands', 'Sydney, Australia', 'In Transit', 'In Transit (Suez Canal)', 'Rotterdam Port -> Suez Canal -> Singapore -> Sydney Mascot Depot', '2026-11-18', NULL, 'Not yet required', '2026-11-14 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10076', 'Antwerp, Belgium', 'Toronto, Canada', 'Delivered', 'Toronto, Canada Consignee Facility', 'Antwerp Port -> Halifax Port -> Toronto Logistics Terminal', '2026-11-12', NULL, 'Cleared', '2026-11-13 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10077', 'Sao Paulo, Brazil', 'Miami, USA', 'Delivered', 'Miami, USA Consignee Facility', 'Santos Port -> Caribbean Route -> Port of Miami', '2026-11-14', NULL, 'Cleared', '2026-11-13 17:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10078', 'Singapore', 'Amsterdam, Netherlands', 'In Transit', 'In Transit (Doha Hub)', 'Changi Cargo -> Doha Hub -> Amsterdam Schiphol', '2026-11-18', NULL, 'Export clearance completed', '2026-11-14 13:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10079', 'Singapore', 'Amsterdam, Netherlands', 'In Transit', 'In Transit (Doha Hub)', 'Changi Cargo -> Doha Hub -> Amsterdam Schiphol', '2026-11-22', NULL, 'Export clearance completed', '2026-11-14 15:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10080', 'Mumbai, India', 'London, UK', 'In Transit', 'In Transit (Dubai Hub)', 'Mumbai Hub -> Dubai Hub -> London Heathrow Hub', '2026-11-18', NULL, 'Duty payment processing', '2026-11-14 15:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10081', 'Chennai, India', 'Singapore', 'On Hold - Customs', 'Singapore International Customs Exam Station', 'Chennai Port -> Port of Singapore -> Jurong Logistics Hub', '2026-11-21', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 18:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10082', 'Bangalore, India', 'San Francisco, USA', 'In Transit', 'In Transit (Singapore)', 'Bangalore Air Cargo -> Singapore -> SFO Air Freight', '2026-11-21', NULL, 'Export clearance completed', '2026-11-14 11:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10083', 'Chennai, India', 'Singapore', 'On Hold - Customs', 'Singapore International Customs Exam Station', 'Chennai Port -> Port of Singapore -> Jurong Logistics Hub', '2026-11-18', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 15:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10084', 'Frankfurt, Germany', 'Tokyo, Japan', 'In Transit', 'In Transit (Dubai Cargo Hub)', 'Frankfurt Airport -> Dubai Cargo Hub -> Tokyo Narita Hub', '2026-11-22', NULL, 'Duty payment processing', '2026-11-14 14:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10085', 'Rotterdam, Netherlands', 'Sydney, Australia', 'Out for Delivery', 'Sydney, Australia Local Delivery Center', 'Rotterdam Port -> Suez Canal -> Singapore -> Sydney Mascot Depot', '2026-11-15', NULL, 'Cleared', '2026-11-14 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10086', 'Dubai, UAE', 'New York, USA', 'Out for Delivery', 'New York, USA Local Delivery Center', 'Dubai Logistics City -> Frankfurt Airport -> JFK Cargo Center', '2026-11-15', NULL, 'Cleared', '2026-11-14 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10087', 'Bangalore, India', 'San Francisco, USA', 'In Transit', 'In Transit (Singapore)', 'Bangalore Air Cargo -> Singapore -> SFO Air Freight', '2026-11-21', NULL, 'Duty payment processing', '2026-11-14 11:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10088', 'Bangalore, India', 'San Francisco, USA', 'On Hold - Customs', 'San Francisco International Customs Exam Station', 'Bangalore Air Cargo -> Singapore -> SFO Air Freight', '2026-11-22', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 15:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10089', 'Singapore', 'Amsterdam, Netherlands', 'In Transit', 'In Transit (Doha Hub)', 'Changi Cargo -> Doha Hub -> Amsterdam Schiphol', '2026-11-17', NULL, 'Duty payment processing', '2026-11-14 17:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10090', 'Chennai, India', 'Singapore', 'On Hold - Customs', 'Singapore International Customs Exam Station', 'Chennai Port -> Port of Singapore -> Jurong Logistics Hub', '2026-11-18', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10091', 'Melbourne, Australia', 'Auckland, New Zealand', 'In Transit', 'In Transit (Tasman Sea Route)', 'Melbourne Port -> Tasman Sea Route -> Auckland Wharf', '2026-11-19', NULL, 'Not yet required', '2026-11-14 23:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10092', 'Delhi, India', 'Chicago, USA', 'In Transit', 'In Transit (London Heathrow)', 'Delhi Air Cargo -> London Heathrow -> Chicago O''Hare Hub', '2026-11-17', NULL, 'Export clearance completed', '2026-11-14 11:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10093', 'Singapore', 'Amsterdam, Netherlands', 'In Transit', 'In Transit (Doha Hub)', 'Changi Cargo -> Doha Hub -> Amsterdam Schiphol', '2026-11-22', NULL, 'Duty payment processing', '2026-11-14 13:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10094', 'Johannesburg, South Africa', 'London, UK', 'In Transit', 'In Transit (Nairobi Hub)', 'O.R. Tambo Airport -> Nairobi Hub -> London Heathrow', '2026-11-17', NULL, 'Not yet required', '2026-11-14 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10095', 'Dubai, UAE', 'New York, USA', 'Delivered', 'New York, USA Consignee Facility', 'Dubai Logistics City -> Frankfurt Airport -> JFK Cargo Center', '2026-11-12', NULL, 'Cleared', '2026-11-13 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10096', 'Zurich, Switzerland', 'Boston, USA', 'Delivered', 'Boston, USA Consignee Facility', 'Zurich Airport -> Dublin Hub -> Boston Logan Freight', '2026-11-12', NULL, 'Cleared', '2026-11-12 14:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10097', 'Sao Paulo, Brazil', 'Miami, USA', 'In Transit', 'In Transit (Caribbean Route)', 'Santos Port -> Caribbean Route -> Port of Miami', '2026-11-19', NULL, 'Duty payment processing', '2026-11-14 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10098', 'Chennai, India', 'Singapore', 'Delayed', 'Transit Hub near Chennai', 'Chennai Port -> Port of Singapore -> Jurong Logistics Hub', '2026-11-27', 'Port congestion and vessel berthing backlog', 'Duty payment processing', '2026-11-14 01:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10099', 'Delhi, India', 'Chicago, USA', 'In Transit', 'In Transit (London Heathrow)', 'Delhi Air Cargo -> London Heathrow -> Chicago O''Hare Hub', '2026-11-21', NULL, 'Not yet required', '2026-11-14 14:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10100', 'Shenzhen, China', 'Paris, France', 'Delayed', 'Transit Hub near Shenzhen', 'Shenzhen Yantian -> Colombo Port -> Le Havre -> Paris Hub', '2026-11-23', 'Port congestion and vessel berthing backlog', 'Export clearance completed', '2026-11-14 06:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10101', 'Antwerp, Belgium', 'Toronto, Canada', 'Delayed', 'Transit Hub near Antwerp', 'Antwerp Port -> Halifax Port -> Toronto Logistics Terminal', '2026-11-23', 'Partner airline mechanical inspection delay', 'Inspection required - Physical examination scheduled', '2026-11-14 05:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10102', 'Rotterdam, Netherlands', 'Sydney, Australia', 'In Transit', 'In Transit (Suez Canal)', 'Rotterdam Port -> Suez Canal -> Singapore -> Sydney Mascot Depot', '2026-11-22', NULL, 'Duty payment processing', '2026-11-14 13:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10103', 'Dubai, UAE', 'New York, USA', 'Delivered', 'New York, USA Consignee Facility', 'Dubai Logistics City -> Frankfurt Airport -> JFK Cargo Center', '2026-11-12', NULL, 'Cleared', '2026-11-12 15:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10104', 'Mumbai, India', 'London, UK', 'In Transit', 'In Transit (Dubai Hub)', 'Mumbai Hub -> Dubai Hub -> London Heathrow Hub', '2026-11-22', NULL, 'Not yet required', '2026-11-14 11:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10105', 'Taipei, Taiwan', 'Munich, Germany', 'Delivered', 'Munich, Germany Consignee Facility', 'Taoyuan Airport -> Frankfurt Hub -> Munich Cargo Terminal', '2026-11-12', NULL, 'Cleared', '2026-11-12 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10106', 'Melbourne, Australia', 'Auckland, New Zealand', 'Delayed', 'Transit Hub near Melbourne', 'Melbourne Port -> Tasman Sea Route -> Auckland Wharf', '2026-11-21', 'Highway transit disruption and road transport detour', 'Inspection required - Physical examination scheduled', '2026-11-14 01:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10107', 'Shanghai, China', 'Los Angeles, USA', 'In Transit', 'In Transit (Long Beach Port)', 'Shanghai Port -> Long Beach Port -> LA Intermodal Depot', '2026-11-21', NULL, 'Duty payment processing', '2026-11-14 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10108', 'Hamburg, Germany', 'Mumbai, India', 'Delayed', 'Transit Hub near Hamburg', 'Hamburg Port -> Suez Transit -> JNPT Mumbai', '2026-11-21', 'Severe weather and typhoon diversion in Pacific corridor', 'Not yet required', '2026-11-14 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10109', 'Chennai, India', 'Singapore', 'In Transit', 'In Transit (Port of Singapore)', 'Chennai Port -> Port of Singapore -> Jurong Logistics Hub', '2026-11-17', NULL, 'Export clearance completed', '2026-11-14 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10110', 'Bangalore, India', 'San Francisco, USA', 'On Hold - Customs', 'San Francisco International Customs Exam Station', 'Bangalore Air Cargo -> Singapore -> SFO Air Freight', '2026-11-21', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10111', 'Hong Kong', 'Frankfurt, Germany', 'Delivered', 'Frankfurt, Germany Consignee Facility', 'Hong Kong Air Cargo -> Dubai -> Frankfurt CargoCity', '2026-11-13', NULL, 'Cleared', '2026-11-13 23:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10112', 'Frankfurt, Germany', 'Tokyo, Japan', 'Delayed', 'Transit Hub near Frankfurt', 'Frankfurt Airport -> Dubai Cargo Hub -> Tokyo Narita Hub', '2026-11-27', 'Severe weather and typhoon diversion in Pacific corridor', 'Not yet required', '2026-11-14 08:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10113', 'Chennai, India', 'Singapore', 'Delivered', 'Singapore Consignee Facility', 'Chennai Port -> Port of Singapore -> Jurong Logistics Hub', '2026-11-14', NULL, 'Cleared', '2026-11-12 21:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10114', 'Melbourne, Australia', 'Auckland, New Zealand', 'Delayed', 'Transit Hub near Melbourne', 'Melbourne Port -> Tasman Sea Route -> Auckland Wharf', '2026-11-24', 'Highway transit disruption and road transport detour', 'Duty payment processing', '2026-11-14 08:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10115', 'Zurich, Switzerland', 'Boston, USA', 'On Hold - Customs', 'Boston International Customs Exam Station', 'Zurich Airport -> Dublin Hub -> Boston Logan Freight', '2026-11-21', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 09:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10116', 'Johannesburg, South Africa', 'London, UK', 'Delivered', 'London, UK Consignee Facility', 'O.R. Tambo Airport -> Nairobi Hub -> London Heathrow', '2026-11-13', NULL, 'Cleared', '2026-11-12 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10117', 'Singapore', 'Amsterdam, Netherlands', 'Delayed', 'Transit Hub near Singapore', 'Changi Cargo -> Doha Hub -> Amsterdam Schiphol', '2026-11-23', 'Peak holiday cargo sorting backlog at gateway facility', 'Export clearance completed', '2026-11-14 06:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10118', 'Doha, Qatar', 'Madrid, Spain', 'Delivered', 'Madrid, Spain Consignee Facility', 'Doha Hamad Airport -> Rome Transit -> Madrid Barajas Hub', '2026-11-12', NULL, 'Cleared', '2026-11-12 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10119', 'Antwerp, Belgium', 'Toronto, Canada', 'In Transit', 'In Transit (Halifax Port)', 'Antwerp Port -> Halifax Port -> Toronto Logistics Terminal', '2026-11-21', NULL, 'Export clearance completed', '2026-11-14 15:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10120', 'Shanghai, China', 'Los Angeles, USA', 'In Transit', 'In Transit (Long Beach Port)', 'Shanghai Port -> Long Beach Port -> LA Intermodal Depot', '2026-11-22', NULL, 'Not yet required', '2026-11-14 12:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10121', 'Rotterdam, Netherlands', 'Sydney, Australia', 'Delayed', 'Transit Hub near Rotterdam', 'Rotterdam Port -> Suez Canal -> Singapore -> Sydney Mascot Depot', '2026-11-25', 'Port congestion and vessel berthing backlog', 'Inspection required - Physical examination scheduled', '2026-11-14 12:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10122', 'Johannesburg, South Africa', 'London, UK', 'Delivered', 'London, UK Consignee Facility', 'O.R. Tambo Airport -> Nairobi Hub -> London Heathrow', '2026-11-14', NULL, 'Cleared', '2026-11-13 17:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10123', 'Hong Kong', 'Frankfurt, Germany', 'Out for Delivery', 'Frankfurt, Germany Local Delivery Center', 'Hong Kong Air Cargo -> Dubai -> Frankfurt CargoCity', '2026-11-15', NULL, 'Cleared', '2026-11-14 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10124', 'Mumbai, India', 'London, UK', 'On Hold - Customs', 'London International Customs Exam Station', 'Mumbai Hub -> Dubai Hub -> London Heathrow Hub', '2026-11-21', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 10:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10125', 'Doha, Qatar', 'Madrid, Spain', 'In Transit', 'In Transit (Rome Transit)', 'Doha Hamad Airport -> Rome Transit -> Madrid Barajas Hub', '2026-11-20', NULL, 'Export clearance completed', '2026-11-14 11:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10126', 'Hong Kong', 'Frankfurt, Germany', 'On Hold - Customs', 'Frankfurt International Customs Exam Station', 'Hong Kong Air Cargo -> Dubai -> Frankfurt CargoCity', '2026-11-20', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 15:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10127', 'Doha, Qatar', 'Madrid, Spain', 'In Transit', 'In Transit (Rome Transit)', 'Doha Hamad Airport -> Rome Transit -> Madrid Barajas Hub', '2026-11-23', NULL, 'Export clearance completed', '2026-11-14 23:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10128', 'Hong Kong', 'Frankfurt, Germany', 'In Transit', 'In Transit (Dubai)', 'Hong Kong Air Cargo -> Dubai -> Frankfurt CargoCity', '2026-11-22', NULL, 'Duty payment processing', '2026-11-14 12:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10129', 'Dubai, UAE', 'New York, USA', 'On Hold - Customs', 'New York International Customs Exam Station', 'Dubai Logistics City -> Frankfurt Airport -> JFK Cargo Center', '2026-11-18', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10130', 'Hong Kong', 'Frankfurt, Germany', 'Delivered', 'Frankfurt, Germany Consignee Facility', 'Hong Kong Air Cargo -> Dubai -> Frankfurt CargoCity', '2026-11-14', NULL, 'Cleared', '2026-11-13 17:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10131', 'Rotterdam, Netherlands', 'Sydney, Australia', 'On Hold - Customs', 'Sydney International Customs Exam Station', 'Rotterdam Port -> Suez Canal -> Singapore -> Sydney Mascot Depot', '2026-11-18', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 21:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10132', 'Singapore', 'Amsterdam, Netherlands', 'In Transit', 'In Transit (Doha Hub)', 'Changi Cargo -> Doha Hub -> Amsterdam Schiphol', '2026-11-23', NULL, 'Not yet required', '2026-11-14 18:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10133', 'Shenzhen, China', 'Paris, France', 'Delayed', 'Transit Hub near Shenzhen', 'Shenzhen Yantian -> Colombo Port -> Le Havre -> Paris Hub', '2026-11-25', 'Documentation discrepancy on commercial invoice', 'Under review - Documentation pending', '2026-11-14 14:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10134', 'Shanghai, China', 'Los Angeles, USA', 'Delivered', 'Los Angeles, USA Consignee Facility', 'Shanghai Port -> Long Beach Port -> LA Intermodal Depot', '2026-11-14', NULL, 'Cleared', '2026-11-12 20:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10135', 'Shanghai, China', 'Los Angeles, USA', 'Delayed', 'Transit Hub near Shanghai', 'Shanghai Port -> Long Beach Port -> LA Intermodal Depot', '2026-11-19', 'Customs secondary inspection and valuation audit', 'Cleared', '2026-11-14 15:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10136', 'Delhi, India', 'Chicago, USA', 'On Hold - Customs', 'Chicago International Customs Exam Station', 'Delhi Air Cargo -> London Heathrow -> Chicago O''Hare Hub', '2026-11-21', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 18:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10137', 'Hamburg, Germany', 'Mumbai, India', 'In Transit', 'In Transit (Suez Transit)', 'Hamburg Port -> Suez Transit -> JNPT Mumbai', '2026-11-17', NULL, 'Duty payment processing', '2026-11-14 14:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10138', 'Delhi, India', 'Chicago, USA', 'Delivered', 'Chicago, USA Consignee Facility', 'Delhi Air Cargo -> London Heathrow -> Chicago O''Hare Hub', '2026-11-12', NULL, 'Cleared', '2026-11-12 21:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10139', 'Zurich, Switzerland', 'Boston, USA', 'Delivered', 'Boston, USA Consignee Facility', 'Zurich Airport -> Dublin Hub -> Boston Logan Freight', '2026-11-14', NULL, 'Cleared', '2026-11-13 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10140', 'Frankfurt, Germany', 'Tokyo, Japan', 'Delivered', 'Tokyo, Japan Consignee Facility', 'Frankfurt Airport -> Dubai Cargo Hub -> Tokyo Narita Hub', '2026-11-12', NULL, 'Cleared', '2026-11-12 17:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10141', 'Delhi, India', 'Chicago, USA', 'In Transit', 'In Transit (London Heathrow)', 'Delhi Air Cargo -> London Heathrow -> Chicago O''Hare Hub', '2026-11-19', NULL, 'Duty payment processing', '2026-11-14 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10142', 'Antwerp, Belgium', 'Toronto, Canada', 'On Hold - Customs', 'Toronto International Customs Exam Station', 'Antwerp Port -> Halifax Port -> Toronto Logistics Terminal', '2026-11-21', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10143', 'Taipei, Taiwan', 'Munich, Germany', 'Delayed', 'Transit Hub near Taipei', 'Taoyuan Airport -> Frankfurt Hub -> Munich Cargo Terminal', '2026-11-25', 'Partner airline mechanical inspection delay', 'Duty payment processing', '2026-11-14 01:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10144', 'Busan, South Korea', 'Vancouver, Canada', 'In Transit', 'In Transit (Pacific Route)', 'Busan Port -> Pacific Route -> Vancouver Port', '2026-11-21', NULL, 'Duty payment processing', '2026-11-14 23:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10145', 'Bangalore, India', 'San Francisco, USA', 'On Hold - Customs', 'San Francisco International Customs Exam Station', 'Bangalore Air Cargo -> Singapore -> SFO Air Freight', '2026-11-17', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 09:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10146', 'Busan, South Korea', 'Vancouver, Canada', 'Delivered', 'Vancouver, Canada Consignee Facility', 'Busan Port -> Pacific Route -> Vancouver Port', '2026-11-11', NULL, 'Cleared', '2026-11-13 17:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10147', 'Dubai, UAE', 'New York, USA', 'Delayed', 'Transit Hub near Dubai', 'Dubai Logistics City -> Frankfurt Airport -> JFK Cargo Center', '2026-11-27', 'Customs secondary inspection and valuation audit', 'Under review - Documentation pending', '2026-11-14 07:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10148', 'Melbourne, Australia', 'Auckland, New Zealand', 'Delivered', 'Auckland, New Zealand Consignee Facility', 'Melbourne Port -> Tasman Sea Route -> Auckland Wharf', '2026-11-12', NULL, 'Cleared', '2026-11-12 20:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10149', 'Shanghai, China', 'Los Angeles, USA', 'In Transit', 'In Transit (Long Beach Port)', 'Shanghai Port -> Long Beach Port -> LA Intermodal Depot', '2026-11-19', NULL, 'Export clearance completed', '2026-11-14 11:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10150', 'Melbourne, Australia', 'Auckland, New Zealand', 'Delivered', 'Auckland, New Zealand Consignee Facility', 'Melbourne Port -> Tasman Sea Route -> Auckland Wharf', '2026-11-11', NULL, 'Cleared', '2026-11-12 23:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10151', 'Doha, Qatar', 'Madrid, Spain', 'On Hold - Customs', 'Madrid International Customs Exam Station', 'Doha Hamad Airport -> Rome Transit -> Madrid Barajas Hub', '2026-11-18', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 07:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10152', 'Delhi, India', 'Chicago, USA', 'In Transit', 'In Transit (London Heathrow)', 'Delhi Air Cargo -> London Heathrow -> Chicago O''Hare Hub', '2026-11-21', NULL, 'Export clearance completed', '2026-11-14 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10153', 'Zurich, Switzerland', 'Boston, USA', 'Delayed', 'Transit Hub near Zurich', 'Zurich Airport -> Dublin Hub -> Boston Logan Freight', '2026-11-19', 'Partner airline mechanical inspection delay', 'Duty payment processing', '2026-11-14 06:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10154', 'Delhi, India', 'Chicago, USA', 'In Transit', 'In Transit (London Heathrow)', 'Delhi Air Cargo -> London Heathrow -> Chicago O''Hare Hub', '2026-11-22', NULL, 'Duty payment processing', '2026-11-14 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10155', 'Johannesburg, South Africa', 'London, UK', 'Delayed', 'Transit Hub near Johannesburg', 'O.R. Tambo Airport -> Nairobi Hub -> London Heathrow', '2026-11-26', 'Customs secondary inspection and valuation audit', 'Inspection required - Physical examination scheduled', '2026-11-14 08:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10156', 'Mumbai, India', 'London, UK', 'In Transit', 'In Transit (Dubai Hub)', 'Mumbai Hub -> Dubai Hub -> London Heathrow Hub', '2026-11-22', NULL, 'Not yet required', '2026-11-14 12:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10157', 'Hamburg, Germany', 'Mumbai, India', 'In Transit', 'In Transit (Suez Transit)', 'Hamburg Port -> Suez Transit -> JNPT Mumbai', '2026-11-21', NULL, 'Duty payment processing', '2026-11-14 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10158', 'Johannesburg, South Africa', 'London, UK', 'Delivered', 'London, UK Consignee Facility', 'O.R. Tambo Airport -> Nairobi Hub -> London Heathrow', '2026-11-11', NULL, 'Cleared', '2026-11-12 18:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10159', 'Melbourne, Australia', 'Auckland, New Zealand', 'In Transit', 'In Transit (Tasman Sea Route)', 'Melbourne Port -> Tasman Sea Route -> Auckland Wharf', '2026-11-19', NULL, 'Export clearance completed', '2026-11-14 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10160', 'Delhi, India', 'Chicago, USA', 'In Transit', 'In Transit (London Heathrow)', 'Delhi Air Cargo -> London Heathrow -> Chicago O''Hare Hub', '2026-11-18', NULL, 'Duty payment processing', '2026-11-14 20:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10161', 'Delhi, India', 'Chicago, USA', 'Delayed', 'Transit Hub near Delhi', 'Delhi Air Cargo -> London Heathrow -> Chicago O''Hare Hub', '2026-11-27', 'Partner airline mechanical inspection delay', 'Export clearance completed', '2026-11-14 03:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10162', 'Antwerp, Belgium', 'Toronto, Canada', 'Out for Delivery', 'Toronto, Canada Local Delivery Center', 'Antwerp Port -> Halifax Port -> Toronto Logistics Terminal', '2026-11-15', NULL, 'Cleared', '2026-11-14 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10163', 'Antwerp, Belgium', 'Toronto, Canada', 'In Transit', 'In Transit (Halifax Port)', 'Antwerp Port -> Halifax Port -> Toronto Logistics Terminal', '2026-11-20', NULL, 'Not yet required', '2026-11-14 23:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10164', 'Johannesburg, South Africa', 'London, UK', 'In Transit', 'In Transit (Nairobi Hub)', 'O.R. Tambo Airport -> Nairobi Hub -> London Heathrow', '2026-11-16', NULL, 'Not yet required', '2026-11-14 15:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10165', 'Antwerp, Belgium', 'Toronto, Canada', 'Delayed', 'Transit Hub near Antwerp', 'Antwerp Port -> Halifax Port -> Toronto Logistics Terminal', '2026-11-26', 'Severe weather and typhoon diversion in Pacific corridor', 'Export clearance completed', '2026-11-14 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10166', 'Mumbai, India', 'London, UK', 'Delivered', 'London, UK Consignee Facility', 'Mumbai Hub -> Dubai Hub -> London Heathrow Hub', '2026-11-11', NULL, 'Cleared', '2026-11-12 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10167', 'Shenzhen, China', 'Paris, France', 'In Transit', 'In Transit (Colombo Port)', 'Shenzhen Yantian -> Colombo Port -> Le Havre -> Paris Hub', '2026-11-20', NULL, 'Not yet required', '2026-11-14 10:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10168', 'Doha, Qatar', 'Madrid, Spain', 'In Transit', 'In Transit (Rome Transit)', 'Doha Hamad Airport -> Rome Transit -> Madrid Barajas Hub', '2026-11-22', NULL, 'Not yet required', '2026-11-14 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10169', 'Shanghai, China', 'Los Angeles, USA', 'Delivered', 'Los Angeles, USA Consignee Facility', 'Shanghai Port -> Long Beach Port -> LA Intermodal Depot', '2026-11-14', NULL, 'Cleared', '2026-11-13 21:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10170', 'Taipei, Taiwan', 'Munich, Germany', 'Out for Delivery', 'Munich, Germany Local Delivery Center', 'Taoyuan Airport -> Frankfurt Hub -> Munich Cargo Terminal', '2026-11-15', NULL, 'Cleared', '2026-11-14 23:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10171', 'Hamburg, Germany', 'Mumbai, India', 'In Transit', 'In Transit (Suez Transit)', 'Hamburg Port -> Suez Transit -> JNPT Mumbai', '2026-11-19', NULL, 'Export clearance completed', '2026-11-14 11:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10172', 'Sao Paulo, Brazil', 'Miami, USA', 'In Transit', 'In Transit (Caribbean Route)', 'Santos Port -> Caribbean Route -> Port of Miami', '2026-11-20', NULL, 'Export clearance completed', '2026-11-14 10:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10173', 'Taipei, Taiwan', 'Munich, Germany', 'Out for Delivery', 'Munich, Germany Local Delivery Center', 'Taoyuan Airport -> Frankfurt Hub -> Munich Cargo Terminal', '2026-11-15', NULL, 'Cleared', '2026-11-14 21:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10174', 'Taipei, Taiwan', 'Munich, Germany', 'Delivered', 'Munich, Germany Consignee Facility', 'Taoyuan Airport -> Frankfurt Hub -> Munich Cargo Terminal', '2026-11-14', NULL, 'Cleared', '2026-11-13 20:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10175', 'Singapore', 'Amsterdam, Netherlands', 'Delayed', 'Transit Hub near Singapore', 'Changi Cargo -> Doha Hub -> Amsterdam Schiphol', '2026-11-21', 'Severe weather and typhoon diversion in Pacific corridor', 'Not yet required', '2026-11-14 05:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10176', 'Shanghai, China', 'Los Angeles, USA', 'In Transit', 'In Transit (Long Beach Port)', 'Shanghai Port -> Long Beach Port -> LA Intermodal Depot', '2026-11-23', NULL, 'Export clearance completed', '2026-11-14 12:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10177', 'Zurich, Switzerland', 'Boston, USA', 'Delivered', 'Boston, USA Consignee Facility', 'Zurich Airport -> Dublin Hub -> Boston Logan Freight', '2026-11-14', NULL, 'Cleared', '2026-11-13 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10178', 'Antwerp, Belgium', 'Toronto, Canada', 'Delayed', 'Transit Hub near Antwerp', 'Antwerp Port -> Halifax Port -> Toronto Logistics Terminal', '2026-11-22', 'Documentation discrepancy on commercial invoice', 'Cleared', '2026-11-14 14:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10179', 'Taipei, Taiwan', 'Munich, Germany', 'Delayed', 'Transit Hub near Taipei', 'Taoyuan Airport -> Frankfurt Hub -> Munich Cargo Terminal', '2026-11-20', 'Severe weather and typhoon diversion in Pacific corridor', 'Inspection required - Physical examination scheduled', '2026-11-14 05:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10180', 'Hamburg, Germany', 'Mumbai, India', 'Delivered', 'Mumbai, India Consignee Facility', 'Hamburg Port -> Suez Transit -> JNPT Mumbai', '2026-11-12', NULL, 'Cleared', '2026-11-13 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10181', 'Chennai, India', 'Singapore', 'In Transit', 'In Transit (Port of Singapore)', 'Chennai Port -> Port of Singapore -> Jurong Logistics Hub', '2026-11-20', NULL, 'Export clearance completed', '2026-11-14 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10182', 'Frankfurt, Germany', 'Tokyo, Japan', 'Delivered', 'Tokyo, Japan Consignee Facility', 'Frankfurt Airport -> Dubai Cargo Hub -> Tokyo Narita Hub', '2026-11-12', NULL, 'Cleared', '2026-11-12 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10183', 'Sao Paulo, Brazil', 'Miami, USA', 'Delivered', 'Miami, USA Consignee Facility', 'Santos Port -> Caribbean Route -> Port of Miami', '2026-11-11', NULL, 'Cleared', '2026-11-13 14:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10184', 'Chennai, India', 'Singapore', 'On Hold - Customs', 'Singapore International Customs Exam Station', 'Chennai Port -> Port of Singapore -> Jurong Logistics Hub', '2026-11-22', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 12:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10185', 'Zurich, Switzerland', 'Boston, USA', 'In Transit', 'In Transit (Dublin Hub)', 'Zurich Airport -> Dublin Hub -> Boston Logan Freight', '2026-11-19', NULL, 'Not yet required', '2026-11-14 13:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10186', 'Taipei, Taiwan', 'Munich, Germany', 'Delivered', 'Munich, Germany Consignee Facility', 'Taoyuan Airport -> Frankfurt Hub -> Munich Cargo Terminal', '2026-11-14', NULL, 'Cleared', '2026-11-12 14:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10187', 'Chennai, India', 'Singapore', 'Delayed', 'Transit Hub near Chennai', 'Chennai Port -> Port of Singapore -> Jurong Logistics Hub', '2026-11-27', 'Severe weather and typhoon diversion in Pacific corridor', 'Inspection required - Physical examination scheduled', '2026-11-14 02:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10188', 'Melbourne, Australia', 'Auckland, New Zealand', 'Out for Delivery', 'Auckland, New Zealand Local Delivery Center', 'Melbourne Port -> Tasman Sea Route -> Auckland Wharf', '2026-11-15', NULL, 'Cleared', '2026-11-14 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10189', 'Taipei, Taiwan', 'Munich, Germany', 'Delivered', 'Munich, Germany Consignee Facility', 'Taoyuan Airport -> Frankfurt Hub -> Munich Cargo Terminal', '2026-11-11', NULL, 'Cleared', '2026-11-13 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10190', 'Busan, South Korea', 'Vancouver, Canada', 'Delivered', 'Vancouver, Canada Consignee Facility', 'Busan Port -> Pacific Route -> Vancouver Port', '2026-11-12', NULL, 'Cleared', '2026-11-13 21:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10191', 'Shenzhen, China', 'Paris, France', 'Delivered', 'Paris, France Consignee Facility', 'Shenzhen Yantian -> Colombo Port -> Le Havre -> Paris Hub', '2026-11-11', NULL, 'Cleared', '2026-11-12 17:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10192', 'Johannesburg, South Africa', 'London, UK', 'In Transit', 'In Transit (Nairobi Hub)', 'O.R. Tambo Airport -> Nairobi Hub -> London Heathrow', '2026-11-21', NULL, 'Not yet required', '2026-11-14 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10193', 'Shenzhen, China', 'Paris, France', 'In Transit', 'In Transit (Colombo Port)', 'Shenzhen Yantian -> Colombo Port -> Le Havre -> Paris Hub', '2026-11-16', NULL, 'Export clearance completed', '2026-11-14 13:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10194', 'Johannesburg, South Africa', 'London, UK', 'Delivered', 'London, UK Consignee Facility', 'O.R. Tambo Airport -> Nairobi Hub -> London Heathrow', '2026-11-14', NULL, 'Cleared', '2026-11-13 15:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10195', 'Busan, South Korea', 'Vancouver, Canada', 'Delivered', 'Vancouver, Canada Consignee Facility', 'Busan Port -> Pacific Route -> Vancouver Port', '2026-11-11', NULL, 'Cleared', '2026-11-12 23:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10196', 'Delhi, India', 'Chicago, USA', 'In Transit', 'In Transit (London Heathrow)', 'Delhi Air Cargo -> London Heathrow -> Chicago O''Hare Hub', '2026-11-20', NULL, 'Not yet required', '2026-11-14 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10197', 'Doha, Qatar', 'Madrid, Spain', 'In Transit', 'In Transit (Rome Transit)', 'Doha Hamad Airport -> Rome Transit -> Madrid Barajas Hub', '2026-11-19', NULL, 'Duty payment processing', '2026-11-14 12:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10198', 'Dubai, UAE', 'New York, USA', 'In Transit', 'In Transit (Frankfurt Airport)', 'Dubai Logistics City -> Frankfurt Airport -> JFK Cargo Center', '2026-11-22', NULL, 'Not yet required', '2026-11-14 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10199', 'Hamburg, Germany', 'Mumbai, India', 'Out for Delivery', 'Mumbai, India Local Delivery Center', 'Hamburg Port -> Suez Transit -> JNPT Mumbai', '2026-11-15', NULL, 'Cleared', '2026-11-14 23:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10200', 'Melbourne, Australia', 'Auckland, New Zealand', 'Out for Delivery', 'Auckland, New Zealand Local Delivery Center', 'Melbourne Port -> Tasman Sea Route -> Auckland Wharf', '2026-11-15', NULL, 'Cleared', '2026-11-14 18:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10201', 'Rotterdam, Netherlands', 'Sydney, Australia', 'Delivered', 'Sydney, Australia Consignee Facility', 'Rotterdam Port -> Suez Canal -> Singapore -> Sydney Mascot Depot', '2026-11-12', NULL, 'Cleared', '2026-11-12 17:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10202', 'Doha, Qatar', 'Madrid, Spain', 'Out for Delivery', 'Madrid, Spain Local Delivery Center', 'Doha Hamad Airport -> Rome Transit -> Madrid Barajas Hub', '2026-11-15', NULL, 'Cleared', '2026-11-14 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10203', 'Melbourne, Australia', 'Auckland, New Zealand', 'Delivered', 'Auckland, New Zealand Consignee Facility', 'Melbourne Port -> Tasman Sea Route -> Auckland Wharf', '2026-11-11', NULL, 'Cleared', '2026-11-13 14:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10204', 'Sao Paulo, Brazil', 'Miami, USA', 'Delayed', 'Transit Hub near Sao Paulo', 'Santos Port -> Caribbean Route -> Port of Miami', '2026-11-23', 'Severe weather and typhoon diversion in Pacific corridor', 'Cleared', '2026-11-14 09:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10205', 'Shenzhen, China', 'Paris, France', 'Out for Delivery', 'Paris, France Local Delivery Center', 'Shenzhen Yantian -> Colombo Port -> Le Havre -> Paris Hub', '2026-11-15', NULL, 'Cleared', '2026-11-14 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10206', 'Singapore', 'Amsterdam, Netherlands', 'On Hold - Customs', 'Amsterdam International Customs Exam Station', 'Changi Cargo -> Doha Hub -> Amsterdam Schiphol', '2026-11-19', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 13:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10207', 'Taipei, Taiwan', 'Munich, Germany', 'Delivered', 'Munich, Germany Consignee Facility', 'Taoyuan Airport -> Frankfurt Hub -> Munich Cargo Terminal', '2026-11-11', NULL, 'Cleared', '2026-11-13 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10208', 'Johannesburg, South Africa', 'London, UK', 'Delivered', 'London, UK Consignee Facility', 'O.R. Tambo Airport -> Nairobi Hub -> London Heathrow', '2026-11-12', NULL, 'Cleared', '2026-11-12 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10209', 'Shenzhen, China', 'Paris, France', 'On Hold - Customs', 'Paris International Customs Exam Station', 'Shenzhen Yantian -> Colombo Port -> Le Havre -> Paris Hub', '2026-11-22', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 15:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10210', 'Taipei, Taiwan', 'Munich, Germany', 'In Transit', 'In Transit (Frankfurt Hub)', 'Taoyuan Airport -> Frankfurt Hub -> Munich Cargo Terminal', '2026-11-16', NULL, 'Export clearance completed', '2026-11-14 18:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10211', 'Doha, Qatar', 'Madrid, Spain', 'Delayed', 'Transit Hub near Doha', 'Doha Hamad Airport -> Rome Transit -> Madrid Barajas Hub', '2026-11-25', 'Peak holiday cargo sorting backlog at gateway facility', 'Inspection required - Physical examination scheduled', '2026-11-14 01:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10212', 'Rotterdam, Netherlands', 'Sydney, Australia', 'Delivered', 'Sydney, Australia Consignee Facility', 'Rotterdam Port -> Suez Canal -> Singapore -> Sydney Mascot Depot', '2026-11-14', NULL, 'Cleared', '2026-11-13 15:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10213', 'Taipei, Taiwan', 'Munich, Germany', 'In Transit', 'In Transit (Frankfurt Hub)', 'Taoyuan Airport -> Frankfurt Hub -> Munich Cargo Terminal', '2026-11-23', NULL, 'Not yet required', '2026-11-14 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10214', 'Sao Paulo, Brazil', 'Miami, USA', 'Out for Delivery', 'Miami, USA Local Delivery Center', 'Santos Port -> Caribbean Route -> Port of Miami', '2026-11-15', NULL, 'Cleared', '2026-11-14 23:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10215', 'Rotterdam, Netherlands', 'Sydney, Australia', 'Delivered', 'Sydney, Australia Consignee Facility', 'Rotterdam Port -> Suez Canal -> Singapore -> Sydney Mascot Depot', '2026-11-13', NULL, 'Cleared', '2026-11-13 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10216', 'Singapore', 'Amsterdam, Netherlands', 'In Transit', 'In Transit (Doha Hub)', 'Changi Cargo -> Doha Hub -> Amsterdam Schiphol', '2026-11-22', NULL, 'Duty payment processing', '2026-11-14 13:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10217', 'Shanghai, China', 'Los Angeles, USA', 'On Hold - Customs', 'Los Angeles International Customs Exam Station', 'Shanghai Port -> Long Beach Port -> LA Intermodal Depot', '2026-11-22', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 10:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10218', 'Shenzhen, China', 'Paris, France', 'Delivered', 'Paris, France Consignee Facility', 'Shenzhen Yantian -> Colombo Port -> Le Havre -> Paris Hub', '2026-11-11', NULL, 'Cleared', '2026-11-13 14:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10219', 'Shanghai, China', 'Los Angeles, USA', 'In Transit', 'In Transit (Long Beach Port)', 'Shanghai Port -> Long Beach Port -> LA Intermodal Depot', '2026-11-20', NULL, 'Duty payment processing', '2026-11-14 20:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10220', 'Shanghai, China', 'Los Angeles, USA', 'Delivered', 'Los Angeles, USA Consignee Facility', 'Shanghai Port -> Long Beach Port -> LA Intermodal Depot', '2026-11-14', NULL, 'Cleared', '2026-11-13 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10221', 'Dubai, UAE', 'New York, USA', 'Delayed', 'Transit Hub near Dubai', 'Dubai Logistics City -> Frankfurt Airport -> JFK Cargo Center', '2026-11-24', 'Port congestion and vessel berthing backlog', 'Cleared', '2026-11-14 21:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10222', 'Antwerp, Belgium', 'Toronto, Canada', 'In Transit', 'In Transit (Halifax Port)', 'Antwerp Port -> Halifax Port -> Toronto Logistics Terminal', '2026-11-18', NULL, 'Export clearance completed', '2026-11-14 20:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10223', 'Sao Paulo, Brazil', 'Miami, USA', 'Delivered', 'Miami, USA Consignee Facility', 'Santos Port -> Caribbean Route -> Port of Miami', '2026-11-13', NULL, 'Cleared', '2026-11-13 21:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10224', 'Shanghai, China', 'Los Angeles, USA', 'Delivered', 'Los Angeles, USA Consignee Facility', 'Shanghai Port -> Long Beach Port -> LA Intermodal Depot', '2026-11-11', NULL, 'Cleared', '2026-11-13 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10225', 'Taipei, Taiwan', 'Munich, Germany', 'In Transit', 'In Transit (Frankfurt Hub)', 'Taoyuan Airport -> Frankfurt Hub -> Munich Cargo Terminal', '2026-11-20', NULL, 'Export clearance completed', '2026-11-14 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10226', 'Singapore', 'Amsterdam, Netherlands', 'Delayed', 'Transit Hub near Singapore', 'Changi Cargo -> Doha Hub -> Amsterdam Schiphol', '2026-11-23', 'Peak holiday cargo sorting backlog at gateway facility', 'Inspection required - Physical examination scheduled', '2026-11-14 01:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10227', 'Johannesburg, South Africa', 'London, UK', 'In Transit', 'In Transit (Nairobi Hub)', 'O.R. Tambo Airport -> Nairobi Hub -> London Heathrow', '2026-11-21', NULL, 'Export clearance completed', '2026-11-14 14:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10228', 'Antwerp, Belgium', 'Toronto, Canada', 'Delivered', 'Toronto, Canada Consignee Facility', 'Antwerp Port -> Halifax Port -> Toronto Logistics Terminal', '2026-11-11', NULL, 'Cleared', '2026-11-12 16:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10229', 'Antwerp, Belgium', 'Toronto, Canada', 'In Transit', 'In Transit (Halifax Port)', 'Antwerp Port -> Halifax Port -> Toronto Logistics Terminal', '2026-11-23', NULL, 'Export clearance completed', '2026-11-14 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10230', 'Hamburg, Germany', 'Mumbai, India', 'In Transit', 'In Transit (Suez Transit)', 'Hamburg Port -> Suez Transit -> JNPT Mumbai', '2026-11-20', NULL, 'Export clearance completed', '2026-11-14 12:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10231', 'Antwerp, Belgium', 'Toronto, Canada', 'In Transit', 'In Transit (Halifax Port)', 'Antwerp Port -> Halifax Port -> Toronto Logistics Terminal', '2026-11-22', NULL, 'Duty payment processing', '2026-11-14 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10232', 'Mumbai, India', 'London, UK', 'Delivered', 'London, UK Consignee Facility', 'Mumbai Hub -> Dubai Hub -> London Heathrow Hub', '2026-11-14', NULL, 'Cleared', '2026-11-12 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10233', 'Hamburg, Germany', 'Mumbai, India', 'Delivered', 'Mumbai, India Consignee Facility', 'Hamburg Port -> Suez Transit -> JNPT Mumbai', '2026-11-12', NULL, 'Cleared', '2026-11-13 20:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10234', 'Zurich, Switzerland', 'Boston, USA', 'In Transit', 'In Transit (Dublin Hub)', 'Zurich Airport -> Dublin Hub -> Boston Logan Freight', '2026-11-18', NULL, 'Duty payment processing', '2026-11-14 13:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10235', 'Frankfurt, Germany', 'Tokyo, Japan', 'Out for Delivery', 'Tokyo, Japan Local Delivery Center', 'Frankfurt Airport -> Dubai Cargo Hub -> Tokyo Narita Hub', '2026-11-15', NULL, 'Cleared', '2026-11-14 18:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10236', 'Chennai, India', 'Singapore', 'In Transit', 'In Transit (Port of Singapore)', 'Chennai Port -> Port of Singapore -> Jurong Logistics Hub', '2026-11-16', NULL, 'Export clearance completed', '2026-11-14 14:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10237', 'Busan, South Korea', 'Vancouver, Canada', 'Delayed', 'Transit Hub near Busan', 'Busan Port -> Pacific Route -> Vancouver Port', '2026-11-24', 'Port congestion and vessel berthing backlog', 'Under review - Documentation pending', '2026-11-14 09:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10238', 'Dubai, UAE', 'New York, USA', 'In Transit', 'In Transit (Frankfurt Airport)', 'Dubai Logistics City -> Frankfurt Airport -> JFK Cargo Center', '2026-11-21', NULL, 'Duty payment processing', '2026-11-14 15:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10239', 'Sao Paulo, Brazil', 'Miami, USA', 'Out for Delivery', 'Miami, USA Local Delivery Center', 'Santos Port -> Caribbean Route -> Port of Miami', '2026-11-15', NULL, 'Cleared', '2026-11-14 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10240', 'Singapore', 'Amsterdam, Netherlands', 'Out for Delivery', 'Amsterdam, Netherlands Local Delivery Center', 'Changi Cargo -> Doha Hub -> Amsterdam Schiphol', '2026-11-15', NULL, 'Cleared', '2026-11-14 20:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10241', 'Antwerp, Belgium', 'Toronto, Canada', 'Delayed', 'Transit Hub near Antwerp', 'Antwerp Port -> Halifax Port -> Toronto Logistics Terminal', '2026-11-26', 'Partner airline mechanical inspection delay', 'Cleared', '2026-11-14 20:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10242', 'Rotterdam, Netherlands', 'Sydney, Australia', 'Delayed', 'Transit Hub near Rotterdam', 'Rotterdam Port -> Suez Canal -> Singapore -> Sydney Mascot Depot', '2026-11-25', 'Severe weather and typhoon diversion in Pacific corridor', 'Export clearance completed', '2026-11-14 05:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10243', 'Busan, South Korea', 'Vancouver, Canada', 'In Transit', 'In Transit (Pacific Route)', 'Busan Port -> Pacific Route -> Vancouver Port', '2026-11-16', NULL, 'Export clearance completed', '2026-11-14 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10244', 'Johannesburg, South Africa', 'London, UK', 'In Transit', 'In Transit (Nairobi Hub)', 'O.R. Tambo Airport -> Nairobi Hub -> London Heathrow', '2026-11-20', NULL, 'Export clearance completed', '2026-11-14 14:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10245', 'Hong Kong', 'Frankfurt, Germany', 'On Hold - Customs', 'Frankfurt International Customs Exam Station', 'Hong Kong Air Cargo -> Dubai -> Frankfurt CargoCity', '2026-11-19', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10246', 'Hamburg, Germany', 'Mumbai, India', 'Delivered', 'Mumbai, India Consignee Facility', 'Hamburg Port -> Suez Transit -> JNPT Mumbai', '2026-11-12', NULL, 'Cleared', '2026-11-13 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10247', 'Melbourne, Australia', 'Auckland, New Zealand', 'Out for Delivery', 'Auckland, New Zealand Local Delivery Center', 'Melbourne Port -> Tasman Sea Route -> Auckland Wharf', '2026-11-15', NULL, 'Cleared', '2026-11-14 21:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10248', 'Bangalore, India', 'San Francisco, USA', 'In Transit', 'In Transit (Singapore)', 'Bangalore Air Cargo -> Singapore -> SFO Air Freight', '2026-11-16', NULL, 'Not yet required', '2026-11-14 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10249', 'Doha, Qatar', 'Madrid, Spain', 'In Transit', 'In Transit (Rome Transit)', 'Doha Hamad Airport -> Rome Transit -> Madrid Barajas Hub', '2026-11-18', NULL, 'Not yet required', '2026-11-14 17:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10250', 'Melbourne, Australia', 'Auckland, New Zealand', 'In Transit', 'In Transit (Tasman Sea Route)', 'Melbourne Port -> Tasman Sea Route -> Auckland Wharf', '2026-11-22', NULL, 'Duty payment processing', '2026-11-14 14:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10251', 'Rotterdam, Netherlands', 'Sydney, Australia', 'On Hold - Customs', 'Sydney International Customs Exam Station', 'Rotterdam Port -> Suez Canal -> Singapore -> Sydney Mascot Depot', '2026-11-22', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10252', 'Doha, Qatar', 'Madrid, Spain', 'Delivered', 'Madrid, Spain Consignee Facility', 'Doha Hamad Airport -> Rome Transit -> Madrid Barajas Hub', '2026-11-12', NULL, 'Cleared', '2026-11-13 18:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10253', 'Delhi, India', 'Chicago, USA', 'Delivered', 'Chicago, USA Consignee Facility', 'Delhi Air Cargo -> London Heathrow -> Chicago O''Hare Hub', '2026-11-13', NULL, 'Cleared', '2026-11-12 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10254', 'Busan, South Korea', 'Vancouver, Canada', 'Delivered', 'Vancouver, Canada Consignee Facility', 'Busan Port -> Pacific Route -> Vancouver Port', '2026-11-12', NULL, 'Cleared', '2026-11-13 17:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10255', 'Singapore', 'Amsterdam, Netherlands', 'In Transit', 'In Transit (Doha Hub)', 'Changi Cargo -> Doha Hub -> Amsterdam Schiphol', '2026-11-23', NULL, 'Not yet required', '2026-11-14 22:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10256', 'Delhi, India', 'Chicago, USA', 'Delivered', 'Chicago, USA Consignee Facility', 'Delhi Air Cargo -> London Heathrow -> Chicago O''Hare Hub', '2026-11-14', NULL, 'Cleared', '2026-11-13 18:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10257', 'Hamburg, Germany', 'Mumbai, India', 'Out for Delivery', 'Mumbai, India Local Delivery Center', 'Hamburg Port -> Suez Transit -> JNPT Mumbai', '2026-11-15', NULL, 'Cleared', '2026-11-14 19:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10258', 'Delhi, India', 'Chicago, USA', 'In Transit', 'In Transit (London Heathrow)', 'Delhi Air Cargo -> London Heathrow -> Chicago O''Hare Hub', '2026-11-19', NULL, 'Duty payment processing', '2026-11-14 14:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10259', 'Delhi, India', 'Chicago, USA', 'On Hold - Customs', 'Chicago International Customs Exam Station', 'Delhi Air Cargo -> London Heathrow -> Chicago O''Hare Hub', '2026-11-18', 'Customs documentation audit in progress', 'Under review - Documentation pending', '2026-11-14 12:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;
INSERT INTO public.shipments (shipment_id, origin, destination, status, current_location, route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES ('SHP-10260', 'Rotterdam, Netherlands', 'Sydney, Australia', 'Delayed', 'Transit Hub near Rotterdam', 'Rotterdam Port -> Suez Canal -> Singapore -> Sydney Mascot Depot', '2026-11-23', 'Highway transit disruption and road transport detour', 'Cleared', '2026-11-14 18:00')
ON CONFLICT (shipment_id) DO UPDATE SET status = EXCLUDED.status, current_location = EXCLUDED.current_location, estimated_delivery = EXCLUDED.estimated_delivery, last_updated = EXCLUDED.last_updated;

-- End of Supabase Shipments Seed
