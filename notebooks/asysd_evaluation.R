# install.packages("devtools")
# devtools::install_github("camaradesuk/ASySD")
# install.packages("dplyr")
library(ASySD)
library(dplyr)

filepath <- commandArgs(trailingOnly = TRUE)[1]
# filepath <- "records_pre_merged.csv"

# Print the filepath
cat("Filepath provided:", filepath, "\n")

# Check if the file exists
if (file.exists(filepath)) {
  cat("The file exists.\n")
} else {
  stop("The file does not exist. Please check the filepath.\n")
}

# load citations
citation_data <- load_search(filepath, method="csv") # endnote

# Print column names of citation_data
cat("Column names in citation_data:\n")
print(colnames(citation_data))

# Set ID
citation_data$record_id <- citation_data$ID
citation_data <- citation_data[, -which(names(citation_data) == "ID")]

# deduplicate
dedup_citations <- dedup_citations(citation_data, user_input=1)

# get unique citation dataframe
unique_citations <- dedup_citations$unique

# Set ID
unique_citations$ID <- unique_citations$duplicate_id

# Save unique_citations to CSV
write.csv(unique_citations, file = "notebooks/asysd_merged_df.csv", row.names = FALSE)
