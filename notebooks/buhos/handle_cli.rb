require 'csv'
require 'json'
require 'sequel'
require 'sqlite3'
require_relative 'duplicate_analysis'

# Connect to the mock database instead of SQLite
DB = Sequel.sqlite

# Define the mock structure of the canonical_documents table
DB.create_table(:canonical_documents) do
  primary_key :id
  String :type, size: 255
  String :title, text: true
  String :author, text: true
  String :date, size: 255
  String :journal, text: true
  String :volume, size: 255
  String :number, size: 255
  String :pages, size: 255
  String :book_name, text: true
  String :editors, text: true
  String :proceedings, text: true
  String :place, size: 255
  String :editorial, size: 255
  String :doi, size: 255
  String :wos_id, size: 32
  String :scopus_id, size: 255
  String :ebscohost_id, size: 255
  Integer :year, null: false
  String :journal_abbr, size: 100
  String :abstract, text: true
  Integer :duplicated
  String :url, text: true
  String :scielo_id, size: 255
  String :refworks_id, size: 255
  String :generic_id, size: 255
  String :pmid, size: 255
  String :pubmed_id, size: 255
  String :semantic_scholar_id, size: 255
  String :arxiv_id, size: 255
end

# Define the CanonicalDocument model with validation
class CanonicalDocument < Sequel::Model(DB[:canonical_documents])
  # Allow all fields for mass assignment
  self.strict_param_setting = false

  # Use Sequel's validation plugin
  plugin :validation_helpers

  # Override _save_refresh to avoid issues with the mock database
  def _save_refresh
    self
  end
end

# Method to create CanonicalDocument entries from CSV
def create_canonical_documents_from_csv()
  puts "Current working directory: #{Dir.pwd}"
  csv_file_path = "records.csv"
  csv_data = CSV.read(csv_file_path, headers: true)

  csv_data.each do |row|
    doc_data = row.to_hash  # Convert each row to a hash
    document = CanonicalDocument.new(doc_data)
    document.save
    puts "Document #{document[:id]} saved successfully."
  end
end

if __FILE__ == $0
  method = ARGV[0]  # Method to call (e.g., 'by_doi')
  csv_file_path = ARGV[1]   # CSV input file path

  # if csv_file_path.nil? || csv_file_path.empty?
  #   raise ArgumentError, "No CSV file provided"
  # end

  begin
    # Create CanonicalDocument entries from CSV data
    create_canonical_documents_from_csv()

    # Print the contents of the CanonicalDocument table
    canonical_documents = CanonicalDocument.dataset

    # Create an instance of DuplicateAnalysis using the CanonicalDocument model
    analysis = Buhos::DuplicateAnalysis.new(canonical_documents)

    # Dynamically call the requested method
    result = analysis.send(method)

    # Output the result as valid JSON
    puts result.to_json

  rescue CSV::MalformedCSVError => e
    puts "Error reading CSV file: #{e.message}"
    exit 1
  rescue NoMethodError => e
    puts "Error: Invalid method '#{method}' called."
    exit 1
  end
end
