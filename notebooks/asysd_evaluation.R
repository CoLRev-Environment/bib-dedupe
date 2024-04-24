# install.packages("devtools")
# devtools::install_github("camaradesuk/ASySD")
# install.packages("dplyr")
library(ASySD)
library(dplyr)

# filepath <- "records_pre_merged.csv"

filedir <- args[1]

# load citations
citation_data <- load_search(paste0(filedir, "records_pre_merged.csv"), method="csv") # endnote

# Set ID
citation_data$record_id <- citation_data$ID
citation_data <- citation_data[, -which(names(citation_data) == "ID")]

# deduplicate
dedup_citations <- dedup_citations(citation_data)

# get unique citation dataframe
unique_citations <- dedup_citations$unique

# Set ID
citation_data$ID <- citation_data$record_id

# Save unique_citations to CSV
write.csv(unique_citations, file = "asysd_merged_df.csv", row.names = FALSE)
