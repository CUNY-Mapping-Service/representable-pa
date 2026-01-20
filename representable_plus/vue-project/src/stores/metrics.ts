export const demographicMetrics = [
  // Population metrics
  {
    id: 'pct_hispanic_cen_2020',
    name: 'Hispanic Population',
    description: 'Percentage of Hispanic population',
    category: 'Population',
    icon: '👥',
    isChoroplethLayer: true, // optional , defaults to true
    isKeyMetric: true // optional, defaults to false (sorted to the top)
  },
  {
    id: 'pct_nh_blk_alone_cen_2020',
    name: 'Non-Hispanic Black',
    description: 'Percentage of Non-Hispanic Black population',
    category: 'Population',
    icon: '👥',
  },
  {
    id: 'pct_nh_asian_alone_cen_2020',
    name: 'Non-Hispanic Asian',
    description: 'Percentage of Non-Hispanic Asian population',
    category: 'Population',
    icon: '👥',
  },
  {
    id: 'pct_nh_aian_alone_cen_2020',
    name: 'American Indian/Alaska Native',
    description: 'Percentage of AI/AN population',
    category: 'Population',
    icon: '👥',
  },
  {
    id: 'pct_born_foreign_acs_17_21',
    name: 'Foreign Born',
    description: 'Percentage of foreign-born residents',
    category: 'Population',
    icon: '🌍',
  },
  {
    id: 'pct_prs_blw_pov_lev_acs_17_21',
    name: 'Below Poverty Level',
    description: 'Percentage below poverty line',
    category: 'Economic',
    icon: '💰',
  },

  // Housing metrics
  {
    id: 'pct_rel_family_hhd_cen_2020',
    name: 'Families w/ Children <6',
    description: 'Percentage with young children',
    category: 'Housing',
    icon: '👶',
  },
  {
    id: 'pct_crowd_occp_u_acs_17_21',
    name: 'Crowded Units',
    description: 'Percentage of crowded housing units',
    category: 'Housing',
    icon: '🏠',
  },
  {
    id: 'pct_mlt_u2_9_strc_acs_17_21',
    name: 'Multi-Unit 2-9',
    description: 'Percentage in 2-9 unit buildings',
    category: 'Housing',
    icon: '🏢',
  },
  {
    id: 'pct_mlt_u10p_acs_17_21',
    name: 'Multi-Unit 10+',
    description: 'Percentage in 10+ unit buildings',
    category: 'Housing',
    icon: '🏙️',
  },

  // Language metrics
  {
    id: 'pct_eng_vw_acs_17_21',
    name: 'Limited English',
    description: 'Percentage with limited English',
    category: 'Language',
    icon: '💬',
  },
  {
    id: 'pct_eng_vw_span_acs_17_21',
    name: 'Spanish Speaking',
    description: 'Percentage of Spanish speakers',
    category: 'Language',
    icon: '🗣️',
  },
  {
    id: 'pct_eng_vw_indoeuro_acs_17_21',
    name: 'Indo-European Speaking',
    description: 'Percentage of Indo-European speakers',
    category: 'Language',
    icon: '🗣️',
  },
  {
    id: 'pct_eng_vw_api_acs_17_21',
    name: 'Asian/Pacific Islander Speaking',
    description: 'Percentage of Asian/PI speakers',
    category: 'Language',
    icon: '🗣️',
  },

  // Count metrics
  {
    id: 'tot_population_cen_2020',
    name: 'Total Population',
    description: 'Total population count',
    category: 'Population',
    icon: '📊',
  },
]
