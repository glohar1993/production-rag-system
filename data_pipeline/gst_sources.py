"""
All publicly available GST documents from CBIC, GST Council, and gst.gov.in.
Every URL here is a free public document — no login required.
"""

GST_SOURCES = [

    # ── GST Acts ──────────────────────────────────────────────────────────────
    {
        "url": "https://cbic.gov.in/resources//htdocs-cbec/gst/CGST-Act.pdf",
        "name": "CGST Act 2017",
        "category": "act",
        "doc_type": "gst_act",
        "tags": ["cgst", "act", "central-gst"],
    },
    {
        "url": "https://cbic.gov.in/resources//htdocs-cbec/gst/IGST-Act.pdf",
        "name": "IGST Act 2017",
        "category": "act",
        "doc_type": "gst_act",
        "tags": ["igst", "act", "integrated-gst", "interstate"],
    },
    {
        "url": "https://cbic.gov.in/resources//htdocs-cbec/gst/UTGST-Act.pdf",
        "name": "UTGST Act 2017",
        "category": "act",
        "doc_type": "gst_act",
        "tags": ["utgst", "act", "union-territory"],
    },
    {
        "url": "https://cbic.gov.in/resources//htdocs-cbec/gst/Compensation-Act.pdf",
        "name": "GST Compensation to States Act 2017",
        "category": "act",
        "doc_type": "gst_act",
        "tags": ["compensation", "cess", "states"],
    },

    # ── GST Rules ─────────────────────────────────────────────────────────────
    {
        "url": "https://cbic.gov.in/resources//htdocs-cbec/gst/cgst-rules-28june2017.pdf",
        "name": "CGST Rules 2017",
        "category": "rules",
        "doc_type": "gst_rules",
        "tags": ["cgst", "rules", "registration", "invoice", "returns", "refund"],
    },

    # ── GST Rate Schedule (Goods) ─────────────────────────────────────────────
    {
        "url": "https://cbic.gov.in/resources//htdocs-cbec/gst/Rates-of-tax-on-Goods-as-approved-by-GST-Council.pdf",
        "name": "GST Rate Schedule - Goods",
        "category": "rates",
        "doc_type": "gst_rates",
        "tags": ["rates", "goods", "hsn", "tax-rate", "nil", "5%", "12%", "18%", "28%"],
    },
    {
        "url": "https://cbic.gov.in/resources//htdocs-cbec/gst/Rates-of-tax-on-Services-as-approved-by-GST-Council.pdf",
        "name": "GST Rate Schedule - Services",
        "category": "rates",
        "doc_type": "gst_rates",
        "tags": ["rates", "services", "sac", "tax-rate", "exemption"],
    },

    # ── GST FAQs (CBIC published sector-wise FAQs) ────────────────────────────
    {
        "url": "https://cbic.gov.in/resources//htdocs-cbec/gst/FAQs-on-GST-updated.pdf",
        "name": "GST FAQs - General",
        "category": "faq",
        "doc_type": "gst_faq",
        "tags": ["faq", "general", "registration", "returns", "payment", "refund"],
    },
    {
        "url": "https://cbic.gov.in/resources//htdocs-cbec/gst/faq-gst-it.pdf",
        "name": "GST FAQs - IT Sector",
        "category": "faq",
        "doc_type": "gst_faq",
        "tags": ["faq", "it", "software", "technology", "export", "services"],
    },
    {
        "url": "https://cbic.gov.in/resources//htdocs-cbec/gst/faq-gst-banking.pdf",
        "name": "GST FAQs - Banking & Financial Services",
        "category": "faq",
        "doc_type": "gst_faq",
        "tags": ["faq", "banking", "finance", "insurance", "nbfc", "loan"],
    },
    {
        "url": "https://cbic.gov.in/resources//htdocs-cbec/gst/faq-gst-textile.pdf",
        "name": "GST FAQs - Textile Sector",
        "category": "faq",
        "doc_type": "gst_faq",
        "tags": ["faq", "textile", "garment", "yarn", "fabric"],
    },
    {
        "url": "https://cbic.gov.in/resources//htdocs-cbec/gst/faq-gst-msme.pdf",
        "name": "GST FAQs - MSME",
        "category": "faq",
        "doc_type": "gst_faq",
        "tags": ["faq", "msme", "small-business", "composition", "threshold"],
    },

    # ── Key GST Concepts Guides ───────────────────────────────────────────────
    {
        "url": "https://cbic.gov.in/resources//htdocs-cbec/gst/input-tax-credit.pdf",
        "name": "GST Input Tax Credit Guide",
        "category": "guide",
        "doc_type": "gst_guide",
        "tags": ["itc", "input-tax-credit", "section-16", "section-17", "blocked-credit"],
    },
    {
        "url": "https://cbic.gov.in/resources//htdocs-cbec/gst/refund.pdf",
        "name": "GST Refund Guide",
        "category": "guide",
        "doc_type": "gst_guide",
        "tags": ["refund", "export", "zero-rated", "inverted-duty", "section-54"],
    },
    {
        "url": "https://cbic.gov.in/resources//htdocs-cbec/gst/reverse-charge.pdf",
        "name": "GST Reverse Charge Mechanism Guide",
        "category": "guide",
        "doc_type": "gst_guide",
        "tags": ["rcm", "reverse-charge", "section-9(3)", "section-9(4)", "unregistered"],
    },
    {
        "url": "https://cbic.gov.in/resources//htdocs-cbec/gst/composition-scheme.pdf",
        "name": "GST Composition Scheme Guide",
        "category": "guide",
        "doc_type": "gst_guide",
        "tags": ["composition", "small-business", "1.5-crore", "section-10"],
    },
    {
        "url": "https://cbic.gov.in/resources//htdocs-cbec/gst/e-invoicing.pdf",
        "name": "GST E-Invoicing Guide",
        "category": "guide",
        "doc_type": "gst_guide",
        "tags": ["e-invoice", "irn", "qr-code", "b2b", "e-invoicing"],
    },
    {
        "url": "https://cbic.gov.in/resources//htdocs-cbec/gst/e-way-bill.pdf",
        "name": "GST E-Way Bill Guide",
        "category": "guide",
        "doc_type": "gst_guide",
        "tags": ["e-way-bill", "transport", "movement", "50000", "consignment"],
    },
]


# ── Supplementary text content (hardcoded for reliability) ───────────────────
# These are indexed directly without fetching a URL — key GST knowledge that
# is universally known and doesn't change frequently.

GST_STATIC_KNOWLEDGE = [

    # ── Registration ──────────────────────────────────────────────────────────
    {
        "content": """GST Registration Threshold Limits (as of 2024):
- Goods suppliers: Mandatory registration if annual turnover exceeds ₹40 lakhs (₹20 lakhs for special category states: Manipur, Mizoram, Nagaland, Tripura).
- Service providers: Mandatory registration if annual turnover exceeds ₹20 lakhs (₹10 lakhs for special category states).
- E-commerce operators: Mandatory registration regardless of turnover.
- Inter-state supply: Mandatory registration regardless of turnover.
- Casual taxable persons: Mandatory registration regardless of turnover.
- Persons liable to pay tax under RCM: Mandatory registration.
Registration must be obtained within 30 days of becoming liable. Application is made on GST portal (gst.gov.in) in Form GST REG-01.""",
        "source": "gst_registration_thresholds",
        "doc_type": "gst_knowledge",
        "category": "registration",
        "tags": ["registration", "threshold", "turnover", "20-lakh", "40-lakh", "reg-01"],
    },

    # ── GST Returns ───────────────────────────────────────────────────────────
    {
        "content": """GST Return Filing Calendar and Forms:
- GSTR-1: Outward supplies (sales). Monthly filers: 11th of next month. Quarterly filers (QRMP scheme, turnover ≤ ₹5 crore): 13th of month after quarter end.
- GSTR-3B: Monthly summary return and tax payment. Monthly: 20th of next month. QRMP quarterly filers: 22nd/24th of month after quarter end (staggered by state).
- GSTR-2B: Auto-drafted ITC statement. Generated on 14th of each month. Read-only — no filing required.
- GSTR-9: Annual return. Due: 31st December of following financial year. Mandatory for businesses with turnover > ₹2 crore.
- GSTR-9C: Reconciliation statement (self-certified audit). Due: 31st December. Required if turnover > ₹5 crore.
- GSTR-4: Annual return for Composition Dealers. Due: 30th April after financial year end.
- GSTR-5: Non-resident taxable person. Due: 20th of next month or 7 days after registration expiry.
- GSTR-6: Input Service Distributor. Due: 13th of next month.
- GSTR-7: TDS deductors. Due: 10th of next month.
- GSTR-8: E-commerce operators (TCS). Due: 10th of next month.
Late filing fee: ₹50/day (₹20/day for nil return), maximum ₹10,000 per return.""",
        "source": "gst_return_calendar",
        "doc_type": "gst_knowledge",
        "category": "returns",
        "tags": ["gstr-1", "gstr-3b", "gstr-9", "returns", "due-date", "filing", "annual-return"],
    },

    # ── GST Tax Rates ─────────────────────────────────────────────────────────
    {
        "content": """GST Tax Rate Slabs in India:
GST has 5 tax rate slabs:

NIL (0%): Essential items — fresh vegetables, milk, eggs, curd, bread, salt, fresh meat, fish, books, newspapers, educational services, healthcare services.

5%: Edible oil, sugar, tea, coffee, coal, fertilizers, life-saving drugs, economy class air travel, transportation services.

12%: Processed food, computers, mobile phones (earlier 18%), business class air travel, hotel rooms (₹1000–7500/night).

18%: Most common rate — restaurant services (AC), construction services, financial services, telecom, IT services, electronics, capital goods.

28%: Luxury and sin goods — cars, motorcycles, tobacco, aerated drinks, cement, ACs, dishwashers, washing machines. Additional Compensation Cess applies on top for some items (e.g., cars: 1%–22% extra).

Exports: Zero-rated (0% GST, ITC refundable).
SEZ supplies: Zero-rated.
Exempted: Basic food, health, education — no GST, no ITC on inputs.""",
        "source": "gst_tax_rates",
        "doc_type": "gst_knowledge",
        "category": "rates",
        "tags": ["rates", "5%", "12%", "18%", "28%", "nil", "zero-rated", "slab", "tax-rate"],
    },

    # ── Input Tax Credit ──────────────────────────────────────────────────────
    {
        "content": """GST Input Tax Credit (ITC) — Key Rules:

ELIGIBILITY (Section 16):
- Registered person must have a valid tax invoice or debit note.
- Goods/services must be received.
- Supplier must have filed their GSTR-1 and tax must appear in buyer's GSTR-2B.
- Tax must have been paid to the government by the supplier.
- Buyer must file their GST return.
- ITC must be claimed by 30th November of following financial year or date of filing annual return, whichever is earlier.

BLOCKED CREDITS (Section 17(5) — cannot claim ITC on):
- Motor vehicles (except for specified business use like transport of goods/passengers, driving schools, dealerships).
- Food, beverages, outdoor catering, beauty treatment, health services (except for further supply).
- Membership of clubs, health, fitness centres.
- Travel benefits to employees (leave travel, home travel).
- Works contract for construction of immovable property (except for plant and machinery).
- Goods/services for personal consumption.
- Goods lost, stolen, destroyed, written off, or gifted as free samples.

PROPORTIONATE ITC (Section 17(1) to 17(4)):
- If goods/services used for both taxable and exempt supplies, ITC is allowed only for the proportion used for taxable supplies.
- Formula: ITC to reverse = (Exempt Turnover / Total Turnover) × Total ITC

REVERSAL:
- If supplier not paid within 180 days: ITC must be reversed.
- Can be reclaimed once payment is made.""",
        "source": "gst_itc_rules",
        "doc_type": "gst_knowledge",
        "category": "itc",
        "tags": ["itc", "input-tax-credit", "section-16", "section-17", "blocked-credit", "reversal", "2b"],
    },

    # ── Reverse Charge Mechanism ──────────────────────────────────────────────
    {
        "content": """GST Reverse Charge Mechanism (RCM):

WHAT IS RCM: Under RCM, the recipient of goods/services pays GST instead of the supplier. The supplier does not charge GST; the buyer pays it directly to the government.

SECTION 9(3) — Specified goods/services (always RCM regardless of supplier registration):
Key services under RCM:
- GTA (Goods Transport Agency) services to registered persons.
- Legal services by advocate/firm to business entity.
- Services by a director to the company.
- Insurance agent services.
- Recovery agent services to banks/NBFCs.
- Author/music composer royalties to publishers.
- Security services (except government).
- Services by government/local authority (except specific exempted ones).
- Renting of motor vehicles to corporate bodies.

SECTION 9(4) — Purchase from unregistered person:
Currently, RCM under Section 9(4) applies only to notified categories. Regular purchases from unregistered vendors are not automatically under RCM (as of 2024).

ITC ON RCM:
- ITC is available for RCM paid.
- But ITC can only be used in the same month AFTER the RCM is paid in cash.
- Cannot use ITC balance to pay RCM — must pay in cash first.

REGISTRATION: If a person is only liable to pay tax under RCM, they must register regardless of turnover.""",
        "source": "gst_rcm",
        "doc_type": "gst_knowledge",
        "category": "rcm",
        "tags": ["rcm", "reverse-charge", "section-9(3)", "unregistered", "gta", "advocate", "director"],
    },

    # ── Place of Supply ───────────────────────────────────────────────────────
    {
        "content": """GST Place of Supply Rules:

Place of Supply determines whether a transaction is CGST+SGST (intra-state) or IGST (inter-state).

FOR GOODS (Section 10):
- If goods are delivered: Place of supply = location where goods are delivered.
- If goods are not to be moved: Location of goods at time of delivery.
- If goods are assembled at site: Place of assembly/installation.
- If goods are supplied on board a conveyance (train/ship/aircraft): Location of departure.

FOR SERVICES (Sections 12 & 13):
General rule: Place of supply = Location of service recipient (if registered). If recipient not registered, place of supply = location where service is actually performed.

Key specific rules:
- Immovable property services (construction, rental, architect): Location of property.
- Restaurant/catering services: Where service is actually performed.
- Training/performance events: Where event is held.
- Telecom services: Location of billing address.
- Banking/financial services: Location of account holder.
- Transportation of goods: Location of registered recipient. If unregistered, place of origin.
- Passenger transport: Place of departure.
- Online information services (OIDAR) to non-business recipient: Location of recipient.

INTRA-STATE: Supplier and recipient in same state → CGST + SGST applies.
INTER-STATE: Supplier and recipient in different states → IGST applies.
IMPORTS: Always IGST (treated as inter-state).
EXPORTS: Zero-rated supply.""",
        "source": "gst_place_of_supply",
        "doc_type": "gst_knowledge",
        "category": "place_of_supply",
        "tags": ["place-of-supply", "cgst", "sgst", "igst", "interstate", "intrastate", "section-10", "section-12"],
    },

    # ── E-Way Bill ────────────────────────────────────────────────────────────
    {
        "content": """GST E-Way Bill Rules:

WHEN REQUIRED:
- Movement of goods worth more than ₹50,000 (taxable value) by any mode of transport.
- Mandatory for inter-state movement irrespective of value.
- Some states require intra-state e-way bill for movement within the state above a threshold.
- Not required for exempted goods, goods transported by non-motorised vehicle, goods transported by government railways (consignment note raised).

WHO GENERATES:
- Registered supplier (if supplying).
- Registered recipient (if supplier is unregistered).
- Transporter (if goods handed over for transport without e-way bill).
- E-commerce operator.

VALIDITY:
- Vehicles other than over-dimensional cargo: 1 day for every 200 km (or part thereof).
- Over-dimensional cargo: 1 day for every 20 km.
- Extension possible if goods not delivered due to valid reasons.
- E-way bill can be cancelled within 24 hours if goods not transported.

FORM: Generated on ewaybillgst.gov.in. Contains:
- GSTIN of supplier and recipient
- Place of delivery, HSN code, quantity, value
- Vehicle number and transporter ID

PENALTY: Movement without valid e-way bill can attract penalty of ₹10,000 or tax due (whichever is higher). Goods and vehicle can be detained.""",
        "source": "gst_eway_bill",
        "doc_type": "gst_knowledge",
        "category": "eway_bill",
        "tags": ["e-way-bill", "eway", "transport", "50000", "validity", "ewaybillgst"],
    },

    # ── E-Invoicing ───────────────────────────────────────────────────────────
    {
        "content": """GST E-Invoicing (Electronic Invoice) System:

APPLICABILITY (mandatory for B2B invoices):
- From 1st October 2020: Businesses with turnover > ₹500 crore.
- From 1st January 2021: Turnover > ₹100 crore.
- From 1st April 2021: Turnover > ₹50 crore.
- From 1st October 2022: Turnover > ₹10 crore.
- From 1st August 2023: Turnover > ₹5 crore (current threshold as of 2024).
NOT applicable to: Banks, NBFCs, insurance companies, GTA, passenger transport, multiplex cinemas, B2C transactions.

HOW IT WORKS:
1. Taxpayer generates invoice in their ERP/billing system.
2. Invoice is uploaded to Invoice Registration Portal (IRP): einvoice1.gst.gov.in
3. IRP validates the invoice and generates:
   - IRN (Invoice Reference Number): 64-character unique hash.
   - QR Code containing key invoice details.
   - Digitally signed JSON returned to taxpayer.
4. IRN and QR code are printed on the physical invoice.
5. IRP auto-populates GSTR-1 and E-Way Bill (if required).

BENEFITS:
- No separate GSTR-1 data entry — auto-populated from e-invoices.
- E-way bill auto-generated for eligible supplies.
- Fake invoices eliminated (IRN validation).
- ITC claims become more reliable.

PENALTY for non-compliance: Invoice not valid, ITC not available to buyer, penalty ₹10,000 per invoice.""",
        "source": "gst_einvoicing",
        "doc_type": "gst_knowledge",
        "category": "einvoicing",
        "tags": ["e-invoice", "einvoice", "irn", "irp", "qr-code", "b2b", "5-crore", "e-invoicing"],
    },

    # ── Composition Scheme ────────────────────────────────────────────────────
    {
        "content": """GST Composition Scheme (Section 10):

ELIGIBILITY:
- Manufacturers and traders: Annual turnover ≤ ₹1.5 crore (₹75 lakhs for special category states).
- Restaurants (not serving alcohol): Annual turnover ≤ ₹1.5 crore.
- Service providers (Composition scheme for services — Section 10(2A)): Annual turnover ≤ ₹50 lakhs.
- Cannot opt if: supplying exempt goods, inter-state supplies, e-commerce operators, manufacturers of notified goods (ice cream, pan masala, tobacco).

TAX RATES (on turnover, no ITC):
- Manufacturers: 1% (0.5% CGST + 0.5% SGST).
- Traders: 1% (0.5% CGST + 0.5% SGST).
- Restaurants: 5% (2.5% CGST + 2.5% SGST).
- Service providers (Section 10(2A)): 6% (3% CGST + 3% SGST).

KEY RESTRICTIONS:
- Cannot collect GST from customers (pay from own pocket).
- Cannot claim Input Tax Credit.
- Cannot make inter-state supplies.
- Must display "Composition Taxable Person" on every invoice and at business place.
- Invoice is called "Bill of Supply" not "Tax Invoice".

RETURN: File CMP-08 (quarterly statement) by 18th of month after quarter. File GSTR-4 annually by 30th April.

OPT IN: Form CMP-02 at beginning of financial year. Opt out: Form CMP-04 within 7 days of crossing threshold.""",
        "source": "gst_composition",
        "doc_type": "gst_knowledge",
        "category": "composition",
        "tags": ["composition", "small-business", "1.5-crore", "section-10", "cmp-08", "gstr-4", "bill-of-supply"],
    },

    # ── GST Refund ────────────────────────────────────────────────────────────
    {
        "content": """GST Refund — Complete Guide (Section 54):

WHEN REFUND IS AVAILABLE:
1. Export of goods/services (zero-rated).
2. Deemed exports.
3. Inverted duty structure (GST on inputs higher than GST on output).
4. Excess payment of tax by mistake.
5. Pre-deposit made for appeal.
6. Assessment/provisional assessment finalization.
7. Refund of tax paid on international tourist purchases.
8. Refund of accumulated ITC on zero-rated supplies.

TIME LIMIT: Application must be filed within 2 years from relevant date.

PROCEDURE:
1. File Form RFD-01 on GST portal.
2. Attach supporting documents (invoices, shipping bill for exports, etc.).
3. For exports: Shipping bill filed with Customs becomes automatic refund claim (IGST refund).
4. Provisional refund of 90% within 7 days for zero-rated supplies (within 1 hour in some cases for exporters).
5. Final refund after scrutiny.

INVERTED DUTY STRUCTURE:
Applicable when GST rate on inputs > GST rate on outputs.
Example: Textile inputs at 12%, but fabric output at 5%.
Formula: Maximum Refund = (Adjusted Total Turnover × Net ITC) / Total Turnover — Tax Paid on inverted supplies.

REJECTION: Reasons include non-filing of returns, GSTR-2A mismatch, exports not reported correctly.

INTEREST: If refund not sanctioned within 60 days of receipt of application, interest @ 6% p.a. is payable by government.""",
        "source": "gst_refund",
        "doc_type": "gst_knowledge",
        "category": "refund",
        "tags": ["refund", "export", "zero-rated", "inverted-duty", "rfd-01", "section-54", "ict-refund"],
    },

    # ── TDS under GST ─────────────────────────────────────────────────────────
    {
        "content": """GST TDS (Tax Deducted at Source) — Section 51:

WHO MUST DEDUCT GST TDS:
- Government departments (Central, State, Union Territory).
- Local authorities.
- Governmental agencies.
- Entities notified by government (PSUs, MSME suppliers to government).

WHEN TO DEDUCT:
- On payment to supplier of taxable goods/services where contract value exceeds ₹2.5 lakhs (excluding GST).

RATE: 2% of payment (1% CGST + 1% SGST for intra-state; 2% IGST for inter-state).

PROCEDURE:
- Deductor must be registered on GST portal as TDS deductor.
- File GSTR-7 by 10th of next month.
- Issue TDS certificate in Form GSTR-7A to supplier within 5 days.
- Deductee (supplier) gets credit of TDS in their electronic cash ledger.

NOTE: GST TDS is different from Income Tax TDS. Both may apply on same payment.
Example: Government pays ₹10 lakh to a contractor:
  - Income Tax TDS: 1% or 2% under Section 194C.
  - GST TDS: 2% on taxable value (if contract > ₹2.5L).
  Both are deducted separately.""",
        "source": "gst_tds",
        "doc_type": "gst_knowledge",
        "category": "tds",
        "tags": ["tds", "section-51", "gstr-7", "government", "deduction", "2%", "tds-certificate"],
    },

    # ── GST on Real Estate ────────────────────────────────────────────────────
    {
        "content": """GST on Real Estate:

UNDER CONSTRUCTION PROPERTY:
- Affordable housing: 1% GST (without ITC).
  Conditions: Metro cities — carpet area ≤ 60 sq.m, price ≤ ₹45 lakhs. Non-metro — carpet area ≤ 90 sq.m, price ≤ ₹45 lakhs.
- Other residential: 5% GST (without ITC).
- Commercial property under construction: 12% GST.

COMPLETED PROPERTY (Occupancy Certificate issued):
- NO GST. Sale of ready-to-move-in property (where OC is received before first sale) is not a supply of service — it's sale of immovable property (exempt from GST, subject to Stamp Duty only).

JOINT DEVELOPMENT AGREEMENT (JDA):
- Landowner transfers development rights: Exempt from GST.
- Developer pays GST on flats given to landowner as consideration.

RENTING:
- Residential property for residential use: Exempt from GST.
- Commercial property renting: 18% GST. From July 2022, RCM applies if rented by registered person from unregistered person.

WORKS CONTRACT FOR CONSTRUCTION:
- For government: 12% GST.
- For private: 18% GST.
- For affordable housing: 12% GST.
No ITC available on works contract for construction of immovable property for own use (blocked credit under Section 17(5)).""",
        "source": "gst_real_estate",
        "doc_type": "gst_knowledge",
        "category": "real_estate",
        "tags": ["real-estate", "property", "construction", "affordable-housing", "under-construction", "oc", "works-contract", "renting"],
    },

    # ── GST on Exports ────────────────────────────────────────────────────────
    {
        "content": """GST on Exports and Zero-Rated Supplies:

ZERO-RATED SUPPLY (Section 16 of IGST Act):
- Export of goods.
- Export of services.
- Supply to SEZ (Special Economic Zone) developer or unit.

OPTIONS FOR EXPORTER:
Option 1 — Export under Bond/LUT without paying IGST:
  - Execute Letter of Undertaking (LUT) in Form RFD-11 on GST portal.
  - Export without paying IGST.
  - Claim refund of accumulated ITC.
  - LUT valid for one financial year. Apply before first export of the year.
  - Who can file LUT: Any registered exporter without prosecution history for tax evasion > ₹2.5 crore.

Option 2 — Export with payment of IGST:
  - Charge and pay IGST on export invoice.
  - Claim refund of IGST paid (processed by Customs based on shipping bill).
  - Refund typically received within 7 days if shipping bill and GSTR-1 are matched.

EXPORT OF SERVICES conditions (all 5 must be satisfied):
1. Supplier located in India.
2. Recipient located outside India.
3. Place of supply is outside India.
4. Payment received in convertible foreign exchange (or INR for Nepal/Bhutan).
5. Supplier and recipient are not merely establishments of the same entity.

DEEMED EXPORTS: Supply to EOU, AA holder, EPCG holder — treated as exports for refund purposes.

DOCUMENTS FOR EXPORT:
- Commercial invoice.
- Shipping bill (for goods).
- Bill of Lading / Airway Bill.
- Bank Realization Certificate (for services).
- Foreign Inward Remittance Certificate (FIRC).""",
        "source": "gst_exports",
        "doc_type": "gst_knowledge",
        "category": "exports",
        "tags": ["export", "zero-rated", "lut", "bond", "igst-refund", "sez", "rfd-11", "shipping-bill", "foreign-exchange"],
    },

    # ── HSN Codes ─────────────────────────────────────────────────────────────
    {
        "content": """HSN Code (Harmonised System of Nomenclature) in GST:

WHAT IS HSN: International system for classifying goods. In GST, HSN determines:
1. Tax rate applicable.
2. Exemption eligibility.
3. E-invoicing and e-way bill requirements.

MANDATORY HSN DIGITS:
- Turnover ≤ ₹5 crore: 4-digit HSN in B2B invoices, optional in B2C.
- Turnover > ₹5 crore: 6-digit HSN mandatory.
- Exports/Imports: 8-digit HSN mandatory.

COMMON HSN CHAPTERS (2-digit):
- Chapter 1-5: Live animals, meat, fish, dairy, eggs
- Chapter 6-14: Plants, vegetables, fruits
- Chapter 15: Fats and oils
- Chapter 16-24: Food preparations, beverages, tobacco
- Chapter 25-27: Minerals, ores, fuels
- Chapter 28-38: Chemicals, pharma
- Chapter 39-40: Plastics, rubber
- Chapter 41-43: Leather
- Chapter 44-46: Wood
- Chapter 50-63: Textiles, garments
- Chapter 61-62: Knitted/woven apparel
- Chapter 64-67: Footwear
- Chapter 72-83: Base metals, iron, steel
- Chapter 84-85: Machinery, electrical equipment
- Chapter 86-89: Vehicles, aircraft, ships
- Chapter 90: Optical, medical instruments
- Chapter 94-96: Furniture, toys, miscellaneous
- Chapter 99: Services (SAC codes start with 99)

SAC CODES (Services Accounting Code):
- 9954: Construction services
- 9961-9962: Wholesale/retail trade
- 9971-9972: Financial services
- 9981-9987: Professional services (legal, accounting, IT)
- 9991-9997: Government, education, health, entertainment services""",
        "source": "gst_hsn_codes",
        "doc_type": "gst_knowledge",
        "category": "hsn",
        "tags": ["hsn", "sac", "harmonised-system", "classification", "chapter", "tax-rate", "6-digit", "8-digit"],
    },

    # ── GST Penalties and Interest ────────────────────────────────────────────
    {
        "content": """GST Penalties, Interest, and Late Fees:

INTEREST ON LATE PAYMENT OF TAX (Section 50):
- Rate: 18% per annum.
- Calculated on: Net tax liability (after ITC set-off) paid late.
- From: Day after due date until date of payment.
- For wrongfully availed ITC: 24% per annum.

LATE FILING FEE:
- GSTR-3B and GSTR-1: ₹50/day (₹25 CGST + ₹25 SGST) for returns with tax liability.
- Nil returns: ₹20/day (₹10 CGST + ₹10 SGST).
- Maximum: ₹10,000 per return.
- GSTR-9 (annual): ₹200/day, maximum 0.25% of turnover in the state.

PENALTIES (Section 73 — without fraud/suppression):
- Tax unpaid due to mistake: Tax + Interest + penalty of 10% of tax (minimum ₹10,000).
- Prosecution not applicable.

PENALTIES (Section 74 — with fraud/suppression):
- Tax unpaid due to fraud: Tax + Interest + penalty of 100% of tax.
- Prosecution possible for tax evasion > ₹5 crore.

SPECIFIC OFFENCES AND PENALTIES:
- Failure to register: ₹10,000 or 10% of tax, whichever is higher.
- Issuing invoice without supply (fake invoice): ₹10,000 or 100% of tax.
- Failure to maintain accounts: ₹10,000.
- Failure to provide information to officer: ₹10,000.
- Non-issuance of e-way bill: ₹10,000 or tax, whichever is higher.
- Non-issuance of e-invoice (where applicable): ₹10,000 per invoice.

AMNESTY / WAIVER: Government periodically announces waiver of late fees for old pending returns. Check CBIC notifications for current amnesty schemes.""",
        "source": "gst_penalties",
        "doc_type": "gst_knowledge",
        "category": "penalties",
        "tags": ["penalty", "interest", "late-fee", "section-50", "section-73", "section-74", "18%", "fraud", "evasion"],
    },
]
