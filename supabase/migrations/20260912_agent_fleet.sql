-- Agent fleet seed: citation directories and competitor watchlist.
-- Idempotent. Edit rows freely; agents only read these tables.

insert into directories (name, domain, submission_url, automation_allowed, verification_type, authority_score, relevance_score, total_score)
values
  ('Google Business Profile','google.com/business','https://business.google.com/create',false,'postcard_or_phone',95,85,90),
  ('Bing Places','bingplaces.com','https://www.bingplaces.com',false,'email_or_phone',80,80,80),
  ('Clutch','clutch.co','https://clutch.co/profile/new',false,'manual_review',88,90,89),
  ('DesignRush','designrush.com','https://www.designrush.com/agency/submit',false,'manual_review',70,85,77),
  ('Crunchbase','crunchbase.com','https://www.crunchbase.com/organization/new',false,'email',85,70,77),
  ('G2','g2.com','https://www.g2.com/products/new',false,'domain_verification',90,75,82),
  ('Capterra','capterra.com','https://www.capterra.com/vendors/sign-up',false,'manual_review',85,75,80),
  ('Trustpilot','trustpilot.com','https://business.trustpilot.com/signup',false,'domain_verification',82,70,76),
  ('Yelp for Business','yelp.com','https://biz.yelp.com/signup',false,'phone',78,65,71),
  ('Better Business Bureau','bbb.org','https://www.bbb.org/get-accredited',false,'manual_review',75,60,67),
  ('Foursquare','foursquare.com','https://foursquare.com/venue',false,'claim',60,55,57),
  ('Hotfrog','hotfrog.com','https://www.hotfrog.com/add',true,'email',45,55,50),
  ('Brownbook','brownbook.net','https://www.brownbook.net/add-business',true,'email',40,50,45)
on conflict (name) do nothing;

insert into competitors (name, domain, category, priority)
values
  ('Zapier','zapier.com','platform',2),
  ('Make','make.com','platform',2),
  ('n8n','n8n.io','platform',1),
  ('HubSpot','hubspot.com','platform_crm',3),
  ('Salesforce','salesforce.com','platform_crm',3)
on conflict (domain) do nothing;

-- Add agency-level competitors here as Mopshy identifies them, e.g.:
-- insert into competitors (name, domain, category, priority) values ('Example Agency','exampleagency.com','agency',1) on conflict (domain) do nothing;
