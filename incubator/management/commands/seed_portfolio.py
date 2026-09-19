"""Load LEEMA's real SEDFA portfolio: 16 enterprises across two intake cohorts.

Source: "Full Portfolio Report - Combined SMME cohort: profiles, readiness assessment
and support plan", Leema Township Incubation NPC to SEDFA, report date 16 September
2026, as at 15 September 2026. Cohorts 27 August - 2 September 2026 (9 enterprises)
and 9 - 15 September 2026 (7 enterprises).

What this command deliberately does NOT load
--------------------------------------------
The source report is classified "Confidential - contains personal information (POPIA)".
Two things in it are therefore absent here, because this repository is public and
anything committed to it is published:

  * Contact person, telephone number and email address for every enterprise.
    Capture these through the admin on a private deployment.
  * The per-enterprise "Gaps and risks" assessment. Publishing "cash flow is the core
    operating constraint" beside a named business can cost it the contract it is
    trying to win. The aggregate picture is carried instead.

Employees and turnover at intake are left EMPTY, not zero: the report records at
Section 6 note 5 that the intake form does not capture them. Empty means not captured.

Stage versus relationship
-------------------------
The report classifies each enterprise by its relationship with LEEMA. The Hub's
pipeline stage is a separate axis. Mapping relationship to an opening stage is an
INFERENCE, not something the report states: incubatee -> incubating, reseller and
strategic partner -> onboarded, applicant and exploring -> applicant. Stages are set
through Enterprise.move_to(), so the seeded history records how each one got there.

    python manage.py seed_portfolio          # empty database only
"""
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from incubator.models import Cohort, Enterprise, Programme

E = Enterprise
R, T, M, P, S = E.Relationship, E.Tier, E.Material, E.Province, E.Sector

# Opening stage per relationship. See the module docstring: this is an inference.
OPENING_STAGE = {
    R.INCUBATEE: E.Stage.INCUBATING,
    R.RESELLER: E.Stage.ONBOARDED,
    R.STRATEGIC: E.Stage.ONBOARDED,
    R.TECH_APPLICANT: E.Stage.APPLICANT,
    R.EXPLORING: E.Stage.APPLICANT,
}
# The shortest sanctioned route to each opening stage.
ROUTE = {
    E.Stage.APPLICANT: [],
    E.Stage.ONBOARDED: [E.Stage.SCREENING, E.Stage.ONBOARDED],
    E.Stage.INCUBATING: [E.Stage.SCREENING, E.Stage.ONBOARDED, E.Stage.INCUBATING],
}

C1, C2 = "27 Aug - 2 Sep 2026", "9 - 15 Sep 2026"

PORTFOLIO = [
    dict(
        cohort=C1, name="Reve P Catering", relationship=R.INCUBATEE, readiness_tier=T.STRUCTURING,
        sector=S.HOSPITALITY, province=P.GP, town="Pretoria (Ninapark)", applied_on=date(2026, 8, 28),
        material_readiness=M.UPDATING, jobs_target=10,
        description="Catering and event management services for corporates, government and private clients.",
        products_services="Food meals, fruit baskets, ginger drink; catering, decor hire and event management.",
        customers_market="Individuals, corporates, government. Gauteng and North West provinces.",
        competitive_edge="Price, experience, technical expertise, personal service.",
        goals_challenge="Goals: more customers, premises/equipment, funding, government/corporate contracts. "
                        "Challenge: cash flow and few jobs on the line.",
        target_1_3_years="Occupy, renovate and operate from a granted resort venue, projected to create 10 new jobs.",
        support_sought="Market access, funding readiness, equipment/infrastructure.",
    ),
    dict(
        cohort=C1, name="Far Out Excellent Trading and Projects", relationship=R.RESELLER,
        readiness_tier=T.STRUCTURING, sector=S.ICT, province=P.NW, town="Mafikeng",
        applied_on=date(2026, 8, 27), material_readiness=M.UPDATING, jobs_target=5,
        description="Computer and technology reseller, trading as Far Out Excellent Trading and Projects.",
        products_services="Desktops, laptops, tablets, mini PCs, accessories, networking and printing products; "
                          "setups, configuration, support, upgrades, maintenance, repair, installation.",
        customers_market="Individuals, corporates, schools, government. Mafikeng and surrounding areas.",
        competitive_edge="Price, quality, local availability.",
        goals_challenge="Goals: premises/equipment, funding, government/corporate contracts. Challenge: capital.",
        target_1_3_years="Become a trusted regional technology reseller; hire 5 full-time staff; secure a regular "
                         "corporate supply contract.",
        support_sought="Market access, suppliers, skills/training, distribution.",
    ),
    dict(
        cohort=C1, name="Lomatlhola Trading Enterprise (Pty) Ltd", relationship=R.RESELLER,
        readiness_tier=T.GROWTH_READY, sector=S.SUPPLY, province=P.NW, town="Klerksdorp",
        applied_on=date(2026, 9, 2), material_readiness=M.CURRENT,
        description="Supply and delivery across construction, manufacturing, ICT, professional services, "
                    "transport, repairs and food/hospitality.",
        products_services="Supply and delivery, landscaping design, gardening, office furniture, retail.",
        customers_market="Individuals, corporates, government. North West province.",
        competitive_edge="Price, quality, local availability, technical expertise, speed, personal service, "
                         "specialist products.",
        goals_challenge="Broad improvement goals across marketing, premises, products, staff, technology, funding "
                        "and distribution. Challenge: funding.",
        target_1_3_years="Expand and achieve financial growth.",
        support_sought="Suppliers, skills/training, funding readiness, equipment/infrastructure, distribution.",
    ),
    dict(
        cohort=C1, name="MIDC (Pty) Ltd", relationship=R.EXPLORING, readiness_tier=T.GROWTH_READY,
        sector=S.ICT, province=P.GP, town="Johannesburg", applied_on=date(2026, 9, 2),
        material_readiness=M.CURRENT,
        description="Diversified investments and development; EaziEcom web development; capital raising.",
        products_services="Investment and development services; web development (EaziEcom); capital raising.",
        customers_market="Corporates and enterprises seeking capital and digital services.",
        competitive_edge="Capital-structuring capability combined with in-house digital services.",
        goals_challenge="Challenge: funding and capital deployment.",
        target_1_3_years="Not stated in submission.",
        support_sought="Partnerships and market access.",
    ),
    dict(
        cohort=C1, name="Thakaramo Security Solution and Training", relationship=R.RESELLER,
        readiness_tier=T.GROWTH_READY, sector=S.SECURITY, province=P.NC, town="Kathu",
        applied_on=date(2026, 9, 2), material_readiness=M.CURRENT,
        description="Security solutions and accredited security training.",
        products_services="Guarding and patrolling, CCTV installation and maintenance, alarm systems and "
                          "monitoring, security training Grade E to A, retail.",
        customers_market="Individuals, corporates, government. Northern Cape and North West.",
        competitive_edge="Price, quality, local availability, technical expertise, speed, personal service, "
                         "specialist products, edge-to-edge solutions.",
        goals_challenge="Broad improvement goals across marketing, premises, products, staff, technology, funding "
                        "and distribution. Challenge: funding and market access.",
        target_1_3_years="Expand and achieve financial growth.",
        support_sought="Suppliers, skills/training, funding readiness, equipment/infrastructure, distribution.",
    ),
    dict(
        cohort=C1, name="Lokissa Business Solutions", relationship=R.RESELLER, readiness_tier=T.GROWTH_READY,
        sector=S.ELECTRICAL, province=P.GP, town="Gauteng (Mafikeng area served)",
        applied_on=date(2026, 9, 2), material_readiness=M.CURRENT,
        description="Electrical products and services, trading as Lokissa.",
        products_services="Electrical products; electrical maintenance and installation services.",
        customers_market="Corporates. Mafikeng and surrounding areas.",
        competitive_edge="Price, quality, local availability, technical expertise, speed, reliable and same-day "
                         "services.",
        goals_challenge="Goals: more customers, products/services, technology/IT systems. "
                        "Challenge: bridging to new markets.",
        target_1_3_years="Secure more projects and operational stability.",
        support_sought="Suppliers, partnerships, skills/training, funding readiness, equipment/infrastructure, "
                       "distribution.",
    ),
    dict(
        cohort=C1, name="Moela Energies (Pty) Ltd", relationship=R.INCUBATEE, readiness_tier=T.STRUCTURING,
        sector=S.ENERGY, province=P.NW, town="Mahikeng", applied_on=date(2026, 9, 2),
        material_readiness=M.REGISTRATION,
        description="Petroleum, lubricants and automotive-related components.",
        products_services="Petroleum and automotive products; energy and automotive fitment components.",
        customers_market="Individuals, corporates, schools, government. Mines, farmers, construction, transport "
                         "and plant contractors, government departments.",
        competitive_edge="Price, quality, convenience, local availability, experience, technical expertise, speed, "
                         "personal service; rural development pricing models.",
        goals_challenge="Broad improvement goals across marketing, premises, products, staff, technology, funding "
                        "and distribution. Challenge: financial injection, staff training, equipment and stock for "
                        "expansion.",
        target_1_3_years="Locally and provincially trusted cross-border supplier; competent staff; in-house bursary "
                         "fund; employee shareholding.",
        support_sought="Market access, suppliers, skills/training, funding readiness, equipment/infrastructure, "
                       "distribution.",
    ),
    dict(
        cohort=C1, name="TM Leasure Homes (Pty) Ltd", relationship=R.INCUBATEE, readiness_tier=T.STRUCTURING,
        sector=S.HOSPITALITY, province=P.NW, town="Mahikeng", applied_on=date(2026, 9, 2),
        material_readiness=M.REGISTRATION,
        description="Hospitality, catering and property leasing.",
        products_services="Hospitality and catering; rental units.",
        customers_market="Individuals, corporates, schools, government. Government, private and public sectors.",
        competitive_edge="Price, quality, convenience, local availability, experience, personal service; friendly, "
                         "patient, humble communication.",
        goals_challenge="Broad improvement goals across marketing, premises, products, staff, technology, funding "
                        "and distribution. Challenge: funding, limited resources and product range.",
        target_1_3_years="Establish a local, regional, provincial and international trusted supplier network.",
        support_sought="Market access, suppliers, partnerships, skills/training, funding readiness, "
                       "equipment/infrastructure, distribution.",
    ),
    dict(
        cohort=C1, name="Motsogapele Food Produce", relationship=R.STRATEGIC, readiness_tier=T.FOUNDATION,
        sector=S.AGRO, province=P.NW, town="Mafikeng", applied_on=date(2026, 9, 2),
        material_readiness=M.UPDATING,
        description="Livestock, chicken and vegetable farming.",
        products_services="Small livestock.",
        customers_market="Individuals. Mafikeng and surrounding communities.",
        competitive_edge="Quality, local availability.",
        goals_challenge="Goals: marketing/branding, products/services, funding. "
                        "Challenge: infrastructural development.",
        target_1_3_years="Supply hospitals across the entire North West province.",
        support_sought="Skills/training, funding readiness, equipment/infrastructure.",
    ),
    dict(
        cohort=C2, name="Oageng Creative Agency", relationship=R.INCUBATEE, readiness_tier=T.GROWTH_READY,
        sector=S.ICT, province=P.GP, town="Pretoria", applied_on=date(2026, 9, 9),
        material_readiness=M.CURRENT, jobs_target=5,
        description="Pretoria-based digital and creative services company helping businesses and organisations "
                    "build and strengthen their presence through technology.",
        products_services="Custom websites, e-commerce platforms, mobile applications, business management "
                          "systems, invoicing and payroll systems, digital marketing materials, corporate identity "
                          "packages; website and software development, branding, digital marketing, social media, "
                          "SEO, hosting, domains, business email, system maintenance, analytics, IT support.",
        customers_market="Individuals, corporates, schools. SMEs, start-ups, professional firms, NPOs and "
                         "corporates in Gauteng and nationally needing affordable digital solutions.",
        competitive_edge="Price, quality, convenience, local availability, experience, technical expertise, speed, "
                         "specialist services. Combines creative design with tailored technology.",
        goals_challenge="Goals: staff/skills, funding, government and corporate contracts. Challenge: limited "
                        "working capital restricts hiring, equipment, marketing and capacity for larger contracts.",
        target_1_3_years="Recurring government and corporate contracts; employ and develop at least five young "
                         "professionals; expand software and web services nationally.",
        support_sought="Market access, partnerships, skills/training, funding readiness, equipment/infrastructure.",
    ),
    dict(
        cohort=C2, name="Rata Batho Holdings (Pty) Ltd", relationship=R.TECH_APPLICANT,
        readiness_tier=T.STRUCTURING, sector=S.ELECTRONICS, province=P.NOT_STATED, town="Not stated",
        applied_on=date(2026, 9, 15), material_readiness=M.NOT_CAPTURED,
        description="Technology company expanding an affordable smart Android TV box solution from South Africa "
                    "into Kenya and other African markets. Application ref. LEEMA-20260915-9A9C.",
        products_services="Smart Android TV boxes with a localised content and services subscription. Proposed "
                          "pilot: an initial batch of 1,000 to 2,000 units. Revenue model: direct hardware "
                          "distribution plus an R120 monthly subscription.",
        customers_market="South Africa first, then Kenya and other African markets.",
        competitive_edge="Affordable hardware paired with recurring localised content.",
        goals_challenge="Refine the cross-border scaling strategy and finalise the financial framework for a full "
                        "funding submission.",
        target_1_3_years="Validate hardware performance and regional logistics through a staged pilot.",
        support_sought="Cross-border scaling strategy, collaboration with technical development teams, financial "
                       "framework for a funding submission.",
    ),
    dict(
        cohort=C2, name="Kaborati Holdings", relationship=R.EXPLORING, readiness_tier=T.STRUCTURING,
        sector=S.MANUFACTURING, province=P.GP, town="Gauteng (town not stated)", applied_on=date(2026, 9, 11),
        material_readiness=M.CURRENT,
        description="Manufactures and supplies PPE, specifically women's specialised protective clothing. "
                    "Intake industry was selected as ICT/Technology; see the data-integrity note.",
        products_services="Women's specialised protective clothing, designed around women's anatomy.",
        customers_market="Individuals, corporates, government. Main market: corporates.",
        competitive_edge="Quality, local availability, specialist products. PPE designed around women's anatomy.",
        goals_challenge="Goals: more customers, premises/equipment, funding, government and corporate contracts, "
                        "distribution. Challenge: funding, distribution and sales channels.",
        target_1_3_years="To be producing at mass scale.",
        support_sought="Market access, suppliers, partnerships, skills, funding readiness, "
                       "equipment/infrastructure, distribution.",
    ),
    dict(
        cohort=C2, name="Level 98 Innovations", relationship=R.EXPLORING, readiness_tier=T.STRUCTURING,
        sector=S.ICT, province=P.NW, town="Rustenburg", applied_on=date(2026, 9, 10),
        material_readiness=M.UPDATING,
        description="IT company providing technology solutions.",
        products_services="Water monitoring and diagnostic solutions; software development; training and "
                          "development.",
        customers_market="Corporates, government. Main market: Tshwane Municipality and surrounding areas.",
        competitive_edge="Convenience, specialist services.",
        goals_challenge="Goals: more customers, marketing, premises/equipment, funding, government and corporate "
                        "contracts, distribution. Challenge: funding.",
        target_1_3_years="Expand the market and sales.",
        support_sought="Partnerships, skills, funding readiness, equipment/infrastructure, distribution.",
    ),
    dict(
        cohort=C2, name="Kairos Chem (Pty) Ltd", relationship=R.EXPLORING, readiness_tier=T.FOUNDATION,
        sector=S.SUPPLY, province=P.GP, town="Johannesburg", applied_on=date(2026, 9, 10),
        material_readiness=M.IMPROVEMENT,
        description="Supply and delivery of general goods to various industries; professional services in "
                    "engineering.",
        products_services="Office furniture, stationery, PPE, corporate clothing, tableware, office and building "
                          "consumables; supply and delivery, project management, professional engineering services.",
        customers_market="Individuals, corporates, government. Johannesburg and surrounding areas.",
        competitive_edge="Quality, convenience, local availability, experience, technical expertise, speed, "
                         "personal service. Differentiator not stated.",
        goals_challenge="Goals: more customers, marketing, funding, government and corporate contracts. "
                        "Challenge: competing with more experienced players with greater financial muscle.",
        target_1_3_years="Grow into a medium-to-large enterprise and create employment for black women.",
        support_sought="Market access, funding readiness, equipment/infrastructure.",
    ),
    dict(
        cohort=C2, name="Olacis Co (Pty) Ltd", relationship=R.EXPLORING, readiness_tier=T.FOUNDATION,
        sector=S.SUPPLY, province=P.GP, town="Pretoria", applied_on=date(2026, 9, 10),
        material_readiness=M.IMPROVEMENT,
        description="Supplies business operations essentials. Intake industries were selected as Construction, "
                    "Retail/Wholesale and Food/Hospitality; see the data-integrity note.",
        products_services="Office stationery, toiletries and sanitary consumables, work protective gear.",
        customers_market="Schools, government. Pretoria and surroundings.",
        competitive_edge="Price, quality, convenience. Positions itself as an eco-friendly business.",
        goals_challenge="Goals: products/services, funding, government and corporate contracts. "
                        "Challenge: finance to execute orders, and for hiring and growth.",
        target_1_3_years="Secure public and private sector contracts; hire from previously disadvantaged "
                         "communities.",
        support_sought="Market access, suppliers, partnerships, skills, funding readiness.",
    ),
    dict(
        cohort=C2, name="Sugar Bears", relationship=R.EXPLORING, readiness_tier=T.FOUNDATION,
        sector=S.HOSPITALITY, province=P.MP, town="eMalahleni", applied_on=date(2026, 9, 15),
        material_readiness=M.NONE,
        description="Corporate and social event catering. No trading name stated.",
        products_services="Food for all occasions.",
        customers_market="Individuals, corporates. eMalahleni and surrounding areas.",
        competitive_edge="Price, quality, convenience, local availability. Affordable meals for the required "
                         "numbers.",
        goals_challenge="Goals: more customers, marketing/branding, premises/equipment, staff/skills, funding. "
                        "Challenge: capital.",
        target_1_3_years="Expand services nationwide.",
        support_sought="Partnerships, skills, funding readiness, equipment/infrastructure.",
    ),
]


class Command(BaseCommand):
    help = "Load the 16-enterprise SEDFA portfolio (September 2026). Empty database only."

    @transaction.atomic
    def handle(self, *args, **opts):
        if Enterprise.objects.exists():
            raise CommandError("Database already has enterprises; seed_portfolio is for an empty database.")

        programme = Programme.objects.create(
            name="SEDFA 2026/27 FY Implementation Plan", funder="SEDFA", fy_start_year=2026)
        cohorts = {
            C1: Cohort.objects.create(programme=programme, name=C1,
                                      start_date=date(2026, 8, 27), end_date=date(2026, 9, 2)),
            C2: Cohort.objects.create(programme=programme, name=C2,
                                      start_date=date(2026, 9, 9), end_date=date(2026, 9, 15)),
        }

        for row in PORTFOLIO:
            row = dict(row)
            enterprise = Enterprise.objects.create(cohort=cohorts[row.pop("cohort")], **row)
            for stage in ROUTE[OPENING_STAGE[enterprise.relationship]]:
                enterprise.move_to(stage, reason="Opening stage from the SEDFA portfolio report, 16 September 2026.")

        if opts.get("verbosity", 1):
            self.stdout.write(self.style.SUCCESS(
                f"Loaded {len(PORTFOLIO)} enterprises across {len(cohorts)} cohorts. "
                "Contact details and per-enterprise risk assessments are deliberately not included."))
