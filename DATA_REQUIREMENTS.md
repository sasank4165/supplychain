# Data Requirements for Supply Chain Agentic AI

## Overview

This application requires supply chain operational data stored in AWS Glue Data Catalog and queryable via Amazon Athena. The data should be in CSV or Parquet format stored in Amazon S3.

## Required Tables

### 1. Product Master Data

**Table**: `product`

**Purpose**: Core product information including descriptions, costs, and supplier relationships

**Schema**:
```sql
CREATE EXTERNAL TABLE IF NOT EXISTS `aws-gpl-cog-sc-db`.`product` (
  `product_code` string COMMENT 'Unique product identifier',
  `short_name` string COMMENT 'Short product name',
  `product_description` string COMMENT 'Full product description',
  `product_group` string COMMENT 'Product category/group',
  `supplier_code1` string COMMENT 'Primary supplier code',
  `stock_account` string COMMENT 'Stock account code',
  `date_created` bigint COMMENT 'Creation date (YYYYMMDD)',
  `date_amended` bigint COMMENT 'Last amendment date (YYYYMMDD)',
  `tax_code` string COMMENT 'Tax classification code',
  `standard_cost` double COMMENT 'Standard cost per unit',
  `standard_height` double COMMENT 'Product height',
  `standard_weight` double COMMENT 'Product weight',
  `standard_length` double COMMENT 'Product length',
  `standard_width` double COMMENT 'Product width',
  `stocking_units` string COMMENT 'Unit of measure for stocking',
  `standard_rrp` double COMMENT 'Recommended retail price',
  `order_units` string COMMENT 'Unit of measure for ordering',
  `stock_item` string COMMENT 'Is this a stock item (Y/N)',
  `cost_indicator` string COMMENT 'Cost calculation indicator',
  `back_order` string COMMENT 'Allow back orders (Y/N)',
  `sop_product` string COMMENT 'Sales order processing product',
  `manufactured` string COMMENT 'Is manufactured (Y/N)',
  `sub_product_group` string COMMENT 'Sub-category',
  `analysis_code` string COMMENT 'Analysis code',
  `inner_qty_su` double COMMENT 'Inner quantity per stocking unit',
  `outer_qty_su` double COMMENT 'Outer quantity per stocking unit',
  `qty_on_order_su` double COMMENT 'Quantity on order',
  `freight_class` string COMMENT 'Freight classification',
  `product_capacity_type` string COMMENT 'Capacity type',
  `min_suggestion_qty_su` double COMMENT 'Minimum suggested quantity',
  `conversion_factor` double COMMENT 'Unit conversion factor'
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://your-data-bucket/product/'
TBLPROPERTIES ('skip.header.line.count'='1');
```

**Sample Data**:
```csv
product_code,short_name,product_description,product_group,supplier_code1,stock_account,date_created,date_amended,tax_code,standard_cost,standard_height,standard_weight,standard_length,standard_width,stocking_units,standard_rrp,order_units,stock_item,cost_indicator,back_order,sop_product,manufactured,sub_product_group,analysis_code,inner_qty_su,outer_qty_su,qty_on_order_su,freight_class,product_capacity_type,min_suggestion_qty_su,conversion_factor
P001,Widget A,Standard Widget Type A,WIDGETS,SUP001,STK001,20230101,20240115,TAX1,10.50,5.0,2.5,10.0,8.0,EA,15.99,EA,Y,STD,Y,Y,N,WIDGET-STD,AN001,1,10,0,FC1,STANDARD,10,1.0
P002,Widget B,Premium Widget Type B,WIDGETS,SUP001,STK001,20230115,20240120,TAX1,15.75,6.0,3.0,12.0,10.0,EA,24.99,EA,Y,STD,Y,Y,N,WIDGET-PREM,AN001,1,10,0,FC1,STANDARD,5,1.0
P003,Gadget X,Electronic Gadget X,GADGETS,SUP002,STK002,20230201,20240201,TAX1,45.00,8.0,5.0,15.0,12.0,EA,79.99,EA,Y,STD,N,Y,Y,GADGET-ELEC,AN002,1,5,0,FC2,FRAGILE,2,1.0
```

**Minimum Records**: 100+ products for meaningful analysis

---

### 2. Warehouse Product Inventory

**Table**: `warehouse_product`

**Purpose**: Warehouse-specific inventory levels, stock positions, and reorder parameters

**Schema**:
```sql
CREATE EXTERNAL TABLE IF NOT EXISTS `aws-gpl-cog-sc-db`.`warehouse_product` (
  `warehouse_code` string COMMENT 'Warehouse identifier',
  `product_code` string COMMENT 'Product identifier',
  `stock_account` string COMMENT 'Stock account',
  `daily_opening_stock_su` double COMMENT 'Daily opening stock',
  `opening_datebigint` bigint COMMENT 'Opening date (YYYYMMDD)',
  `period_opening_stock_su` double COMMENT 'Period opening stock',
  `physical_stock_su` double COMMENT 'Physical stock on hand',
  `free_stock_su` double COMMENT 'Available free stock',
  `qty_on_order_su` double COMMENT 'Quantity on order',
  `minimum_stock_su` double COMMENT 'Minimum stock level',
  `maximum_stock_su` double COMMENT 'Maximum stock level',
  `allocated_stock_su` double COMMENT 'Allocated stock',
  `order_qty_su` double COMMENT 'Standard order quantity',
  `standard_ord_qty_su` double COMMENT 'Standard order quantity',
  `standard_cost` double COMMENT 'Standard cost',
  `last_cost` double COMMENT 'Last purchase cost',
  `last_datebigint` bigint COMMENT 'Last transaction date (YYYYMMDD)',
  `lead_time_daysbigint` bigint COMMENT 'Lead time in days',
  `serial_gi` string COMMENT 'Serial number goods in',
  `serial_desp` string COMMENT 'Serial number despatch',
  `expiry_prod` string COMMENT 'Expiry product flag',
  `small_qty_su` double COMMENT 'Small quantity',
  `handling_code` string COMMENT 'Handling code',
  `pick_loc` string COMMENT 'Pick location',
  `pick_store_code` string COMMENT 'Pick store code',
  `last_despatch_date` bigint COMMENT 'Last despatch date',
  `last_received_date` bigint COMMENT 'Last received date',
  `minimum_order_qty` double COMMENT 'Minimum order quantity',
  `maximum_order_qty` double COMMENT 'Maximum order quantity',
  `stock_status` string COMMENT 'Stock status'
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://your-data-bucket/warehouse_product/'
TBLPROPERTIES ('skip.header.line.count'='1');
```

**Sample Data**:
```csv
warehouse_code,product_code,stock_account,daily_opening_stock_su,opening_datebigint,period_opening_stock_su,physical_stock_su,free_stock_su,qty_on_order_su,minimum_stock_su,maximum_stock_su,allocated_stock_su,order_qty_su,standard_ord_qty_su,standard_cost,last_cost,last_datebigint,lead_time_daysbigint,serial_gi,serial_desp,expiry_prod,small_qty_su,handling_code,pick_loc,pick_store_code,last_despatch_date,last_received_date,minimum_order_qty,maximum_order_qty,stock_status
WH01,P001,STK001,100,20240101,100,85,75,50,20,200,10,50,50,10.50,10.25,20240115,7,N,N,N,5,HC1,A-01-01,PS01,20240114,20240110,10,500,ACTIVE
WH01,P002,STK001,50,20240101,50,15,10,30,10,100,5,30,30,15.75,15.50,20240115,7,N,N,N,2,HC1,A-01-02,PS01,20240113,20240108,5,200,ACTIVE
WH02,P001,STK001,150,20240101,150,140,130,0,30,300,10,50,50,10.50,10.25,20240115,7,N,N,N,5,HC1,B-01-01,PS02,20240115,20240112,10,500,ACTIVE
```

**Minimum Records**: 500+ warehouse-product combinations

---

### 3. Sales Order Header

**Table**: `sales_order_header`

**Purpose**: Sales order master information including customer, delivery, and status

**Schema**:
```sql
CREATE EXTERNAL TABLE IF NOT EXISTS `aws-gpl-cog-sc-db`.`sales_order_header` (
  `sales_order_prefix` string COMMENT 'Order prefix',
  `sales_order_number` string COMMENT 'Order number',
  `customer_code` string COMMENT 'Customer identifier',
  `customer_ref` string COMMENT 'Customer reference',
  `deliver_to_customer` string COMMENT 'Delivery customer code',
  `deliver_to_address_no` string COMMENT 'Delivery address number',
  `comment` string COMMENT 'Order comments',
  `currency_code` string COMMENT 'Currency code',
  `currency_ratedouble` double COMMENT 'Currency exchange rate',
  `order_raised_date` bigint COMMENT 'Order date (YYYYMMDD)',
  `pref_del_date` bigint COMMENT 'Preferred delivery date',
  `agent_code` string COMMENT 'Sales agent code',
  `text_code` string COMMENT 'Text code',
  `carrier_code` string COMMENT 'Carrier code',
  `del_area_code` string COMMENT 'Delivery area code',
  `del_seq_number` int COMMENT 'Delivery sequence',
  `posting_year` int COMMENT 'Posting year',
  `posting_period` int COMMENT 'Posting period',
  `last_line_no` int COMMENT 'Last line number',
  `warehouse_code` string COMMENT 'Warehouse code',
  `order_type` string COMMENT 'Order type',
  `forward_order` string COMMENT 'Forward order flag',
  `acknowledge_order` string COMMENT 'Acknowledge flag',
  `free_format` string COMMENT 'Free format flag',
  `order_status` string COMMENT 'Order status',
  `allocate_stock` string COMMENT 'Allocate stock flag',
  `end_cust_name` string COMMENT 'End customer name',
  `end_cust_add_line_1` string COMMENT 'Address line 1',
  `end_cust_add_line_2` string COMMENT 'Address line 2',
  `end_cust_add_line_3` string COMMENT 'Address line 3',
  `end_cust_add_line_4` string COMMENT 'Address line 4',
  `part_request_seq` int COMMENT 'Part request sequence',
  `sales_product_type` string COMMENT 'Product type',
  `patch_id` string COMMENT 'Patch ID',
  `postcode_sector` string COMMENT 'Postcode sector',
  `customer_id` string COMMENT 'Customer ID',
  `payment_received` string COMMENT 'Payment received flag',
  `carriage_charge` double COMMENT 'Carriage charge',
  `payment_type` string COMMENT 'Payment type'
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://your-data-bucket/sales_order_header/'
TBLPROPERTIES ('skip.header.line.count'='1');
```

**Sample Data**:
```csv
sales_order_prefix,sales_order_number,customer_code,customer_ref,deliver_to_customer,deliver_to_address_no,comment,currency_code,currency_ratedouble,order_raised_date,pref_del_date,agent_code,text_code,carrier_code,del_area_code,del_seq_number,posting_year,posting_period,last_line_no,warehouse_code,order_type,forward_order,acknowledge_order,free_format,order_status,allocate_stock,end_cust_name,end_cust_add_line_1,end_cust_add_line_2,end_cust_add_line_3,end_cust_add_line_4,part_request_seq,sales_product_type,patch_id,postcode_sector,customer_id,payment_received,carriage_charge,payment_type
SO,SO001,CUST001,REF001,CUST001,ADDR001,Rush order,USD,1.0,20240110,20240115,AG001,TXT001,CARR001,AREA01,1,2024,1,3,WH01,STANDARD,N,Y,N,PICKING,Y,ABC Company,123 Main St,Suite 100,New York,NY 10001,1,STANDARD,P001,10001,CUST001,N,15.00,CREDIT
SO,SO002,CUST002,REF002,CUST002,ADDR002,,USD,1.0,20240111,20240116,AG002,TXT001,CARR001,AREA02,1,2024,1,2,WH01,STANDARD,N,Y,N,PACKED,Y,XYZ Corp,456 Oak Ave,,Los Angeles,CA 90001,1,STANDARD,P002,90001,CUST002,N,12.00,CREDIT
```

**Minimum Records**: 1000+ orders for trend analysis

---

### 4. Sales Order Line

**Table**: `sales_order_line`

**Purpose**: Line item details for sales orders including quantities and fulfillment status

**Schema**:
```sql
CREATE EXTERNAL TABLE IF NOT EXISTS `aws-gpl-cog-sc-db`.`sales_order_line` (
  `sales_order_prefix` string,
  `sales_order_number` string,
  `sales_order_line` int,
  `product_code` string,
  `desc` string,
  `stocking_units` string,
  `selling_units` string,
  `qty_seludouble` double COMMENT 'Quantity in selling units',
  `required_delivery_date` bigint,
  `pick_by_date` bigint,
  `unit_price_selu` double,
  `line_value` double,
  `prod_disc1_percentage` double,
  `tax_code` string,
  `cost_value` double,
  `allocated_qty_su` double,
  `qty_ordered_su` double,
  `picked_qty_su` double,
  `despatched_qty_su` double,
  `invoiced_qty_su` double,
  `returned_qty_su` double,
  `qty_cancelled_su` double,
  `value_ord_notinv` double,
  `kit_parent_code` string,
  `kit` string,
  `kit_order_line` int,
  `warehouse_code` string,
  `supply_direct` string,
  `linked_for_despatch` string,
  `schedule_deliveries` string,
  `order_line_status` string,
  `order_indicator` string,
  `price_basis` string,
  `tax_indicator` string,
  `ship_complete` string,
  `ordered_product_code` string,
  `sales_period_no` int,
  `orig_req_qty_su` double
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://your-data-bucket/sales_order_line/'
TBLPROPERTIES ('skip.header.line.count'='1');
```

**Sample Data**:
```csv
sales_order_prefix,sales_order_number,sales_order_line,product_code,desc,stocking_units,selling_units,qty_seludouble,required_delivery_date,pick_by_date,unit_price_selu,line_value,prod_disc1_percentage,tax_code,cost_value,allocated_qty_su,qty_ordered_su,picked_qty_su,despatched_qty_su,invoiced_qty_su,returned_qty_su,qty_cancelled_su,value_ord_notinv,kit_parent_code,kit,kit_order_line,warehouse_code,supply_direct,linked_for_despatch,schedule_deliveries,order_line_status,order_indicator,price_basis,tax_indicator,ship_complete,ordered_product_code,sales_period_no,orig_req_qty_su
SO,SO001,1,P001,Widget A,EA,EA,10,20240115,20240114,15.99,159.90,0,TAX1,105.00,10,10,10,0,0,0,0,159.90,,N,0,WH01,N,N,N,PICKED,STD,LIST,STD,N,P001,1,10
SO,SO001,2,P002,Widget B,EA,EA,5,20240115,20240114,24.99,124.95,0,TAX1,78.75,5,5,5,0,0,0,0,124.95,,N,0,WH01,N,N,N,PICKED,STD,LIST,STD,N,P002,1,5
```

**Minimum Records**: 3000+ line items

---

### 5. Purchase Order Header

**Table**: `purchase_order_header`

**Purpose**: Purchase order master information for procurement

**Schema**:
```sql
CREATE EXTERNAL TABLE IF NOT EXISTS `aws-gpl-cog-sc-db`.`purchase_order_header` (
  `purchase_order_prefix` string,
  `purchase_order_number` string,
  `requisition_number` string,
  `supplier_code` string,
  `supplier_ref` string,
  `delivery_point` string,
  `internal_ref` string,
  `comment` string,
  `currency_code` string,
  `authority_code` string,
  `currency_ratedouble` double,
  `order_raised_date` bigint,
  `posting_year` int,
  `posting_period` int,
  `last_line_no` int,
  `purchase_order_type` string,
  `order_status` string,
  `invoice_status` string,
  `order_released_date` bigint,
  `order_released_time` string,
  `user_id` string
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://your-data-bucket/purchase_order_header/'
TBLPROPERTIES ('skip.header.line.count'='1');
```

**Sample Data**:
```csv
purchase_order_prefix,purchase_order_number,requisition_number,supplier_code,supplier_ref,delivery_point,internal_ref,comment,currency_code,authority_code,currency_ratedouble,order_raised_date,posting_year,posting_period,last_line_no,purchase_order_type,order_status,invoice_status,order_released_date,order_released_time,user_id
PO,PO001,REQ001,SUP001,SUPREF001,WH01,INT001,Standard order,USD,AUTH001,1.0,20240105,2024,1,2,STANDARD,OPEN,PENDING,20240105,10:30:00,USER001
PO,PO002,REQ002,SUP002,SUPREF002,WH01,INT002,Urgent order,USD,AUTH001,1.0,20240106,2024,1,1,URGENT,OPEN,PENDING,20240106,14:15:00,USER002
```

**Minimum Records**: 500+ purchase orders

---

### 6. Purchase Order Line

**Table**: `purchase_order_line`

**Purpose**: Line item details for purchase orders

**Schema**:
```sql
CREATE EXTERNAL TABLE IF NOT EXISTS `aws-gpl-cog-sc-db`.`purchase_order_line` (
  `purchase_order_prefix` string,
  `purchase_order_numberbigint` bigint,
  `purchase_order_linebigint` bigint,
  `requisition_prefix` string,
  `requisition_number` string,
  `product_code` string,
  `supplier_product_ref` string,
  `comment` string,
  `comment_on_receipt` string,
  `method_code` string,
  `order_units` string,
  `qty_oudouble` double,
  `expected_dely_datebigint` bigint,
  `original_dely_datebigint` bigint,
  `unit_price_oudouble` double,
  `line_valuedouble` double,
  `credited_value_oudouble` double,
  `cost_valuedouble` double,
  `cost_qty_oudouble` double,
  `in_receipt_qty_oudouble` double,
  `received_qty_oudouble` double,
  `invoiced_qty_oudouble` double,
  `returned_qty_oudouble` double,
  `in_receipt_qty_sudouble` double,
  `received_qty_sudouble` double,
  `returned_qty_sudouble` double,
  `inspect_comment1` string,
  `completed` string,
  `order_status` string,
  `price_status` string,
  `requisition_linebigint` bigint,
  `ordered_product_code` string
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://your-data-bucket/purchase_order_line/'
TBLPROPERTIES ('skip.header.line.count'='1');
```

**Sample Data**:
```csv
purchase_order_prefix,purchase_order_numberbigint,purchase_order_linebigint,requisition_prefix,requisition_number,product_code,supplier_product_ref,comment,comment_on_receipt,method_code,order_units,qty_oudouble,expected_dely_datebigint,original_dely_datebigint,unit_price_oudouble,line_valuedouble,credited_value_oudouble,cost_valuedouble,cost_qty_oudouble,in_receipt_qty_oudouble,received_qty_oudouble,invoiced_qty_oudouble,returned_qty_oudouble,in_receipt_qty_sudouble,received_qty_sudouble,returned_qty_sudouble,inspect_comment1,completed,order_status,price_status,requisition_linebigint,ordered_product_code
PO,1,1,REQ,REQ001,P001,SUP-P001,Standard order,,STD,EA,100,20240115,20240115,10.25,1025.00,0,1025.00,100,0,0,0,0,0,0,0,,N,OPEN,CONFIRMED,1,P001
PO,1,2,REQ,REQ001,P002,SUP-P002,Standard order,,STD,EA,50,20240115,20240115,15.50,775.00,0,775.00,50,0,0,0,0,0,0,0,,N,OPEN,CONFIRMED,2,P002
```

**Minimum Records**: 1500+ line items

---

## Data Volume Recommendations

### Minimum for Testing
- Products: 100
- Warehouse-Product combinations: 500
- Sales Orders: 500
- Sales Order Lines: 1,500
- Purchase Orders: 200
- Purchase Order Lines: 600

### Recommended for Production
- Products: 1,000+
- Warehouse-Product combinations: 5,000+
- Sales Orders: 10,000+
- Sales Order Lines: 30,000+
- Purchase Orders: 5,000+
- Purchase Order Lines: 15,000+

### Optimal for Analytics
- Products: 10,000+
- Warehouse-Product combinations: 50,000+
- Sales Orders: 100,000+
- Sales Order Lines: 300,000+
- Purchase Orders: 50,000+
- Purchase Order Lines: 150,000+

## Data Quality Requirements

### 1. Referential Integrity
- All `product_code` in warehouse_product must exist in product table
- All `product_code` in order lines must exist in product table
- All `warehouse_code` in orders must exist in warehouse_product

### 2. Date Formats
- All dates stored as BIGINT in YYYYMMDD format
- Example: January 15, 2024 = 20240115

### 3. Numeric Fields
- Quantities: Non-negative doubles
- Costs/Prices: Non-negative doubles with 2 decimal precision
- Percentages: 0-100 range

### 4. Status Values
- Order Status: OPEN, PICKING, PACKED, SHIPPED, COMPLETED, CANCELLED
- Stock Status: ACTIVE, INACTIVE, DISCONTINUED

### 5. Required Fields
- product_code: Must be unique and non-null
- warehouse_code: Must be non-null
- order numbers: Must be unique within prefix
- dates: Must be valid YYYYMMDD format

## Data Freshness

### Real-time Updates (Ideal)
- Warehouse inventory: Updated every 15 minutes
- Order status: Updated on status change
- Stock allocations: Real-time

### Batch Updates (Minimum)
- Daily full refresh at midnight
- Incremental updates every 4 hours
- Historical data: Monthly archives

## Next Steps

See:
- `DATA_SETUP_GUIDE.md` - Step-by-step data loading
- `SAMPLE_DATA_GENERATOR.md` - Generate test data
- `data/` directory - Sample CSV files
