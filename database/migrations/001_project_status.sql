ALTER TABLE Project_Details
  ADD COLUMN Project_Status ENUM('Open','Ongoing','Completed') NOT NULL DEFAULT 'Ongoing',
  ADD COLUMN Completed_At DATETIME NULL;