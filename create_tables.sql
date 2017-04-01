CREATE TABLE Plans (MRN varchar(12), Birthdate date, Age tinyint(3) unsigned, Sex char(1), SimStudyDate date, RadOnc varchar(50), TxSite varchar(50), RxDose float, Fractions tinyint(3) unsigned, Energy varchar(30), StudyInstanceUID varchar(100), PatientOrientation varchar(3), PlanTimeStamp datetime, StTimeStamp datetime, DoseTimeStamp datetime, TPSManufacturer varchar(50), TPSSoftwareName varchar(50), TPSSoftwareVersion varchar(30), TxModality varchar(30), TxTime time, MUs int(6) unsigned, DoseGridRes varchar(16));
CREATE TABLE DVHs (MRN varchar(12), StudyInstanceUID varchar(100), InstitutionalROI VARCHAR(50), PhysicianROI VARCHAR(50), ROIName VARCHAR(50), Type VARCHAR(20), Volume DOUBLE, MinDose DOUBLE, MeanDose DOUBLE, MaxDose DOUBLE, DoseBinSize FLOAT, VolumeString MEDIUMTEXT);
CREATE TABLE Beams (MRN varchar(12), StudyInstanceUID varchar(100), BeamNum smallint(4) unsigned, BeamDescription varchar(30), FxGroup smallint(4) unsigned, Fractions tinyint(3) unsigned, NumFxGrpBeams smallint(4) unsigned, BeamDose DOUBLE unsigned, BeamMUs DOUBLE unsigned, RadiationType varchar(30), BeamEnergy FLOAT unsigned, BeamType varchar(30), ControlPoints smallint(5) unsigned, GantryStart FLOAT, GantryEnd FLOAT, GantryRotDir varchar(3), ColAngle DOUBLE, CouchAngle DOUBLE, IsocenterCoord varchar(30), SSD DOUBLE unsigned);
CREATE TABLE Rxs (MRN varchar(12), StudyInstanceUID varchar(100), FxGrpName varchar(30), FxGrpNum smallint(4) unsigned, FxGrps smallint(4) unsigned, FxDose DOUBLE unsigned, Fxs smallint(4) unsigned, RxDose DOUBLE unsigned, RxPercent DOUBLE unsigned, NormMethod varchar(30), NormObject varchar(30));