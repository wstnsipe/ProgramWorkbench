import type { StandardCatalogEntry } from '../types'

/**
 * Known DoD/industry standards catalog.
 * catalog_id is stable — use for recommendation hooks.
 */
export const STANDARDS_CATALOG: StandardCatalogEntry[] = [
  {
    catalog_id: 'FACE',
    name: 'FACE Technical Standard',
    description: 'Future Airborne Capability Environment — avionics software portability',
    branches: ['USAF', 'USN', 'ARMY'],
  },
  {
    catalog_id: 'SOSA',
    name: 'VITA 65 (SOSA)',
    description: 'Sensor Open Systems Architecture — embedded computing hardware',
    branches: [],
  },
  {
    catalog_id: 'VICTORY',
    name: 'VICTORY',
    description: 'Vehicular Integration for C4ISR/EW Interoperability',
    branches: ['ARMY'],
  },
  {
    catalog_id: 'GVA',
    name: 'Generic Vehicle Architecture (GVA)',
    description: 'UK/allied ground vehicle open architecture standard',
    branches: ['ARMY'],
  },
  {
    catalog_id: 'CMOSS',
    name: 'C5ISR/EW Modular Open Suite of Standards (CMOSS)',
    description: 'Army C5ISR center modular standards suite',
    branches: ['ARMY'],
  },
  {
    catalog_id: 'MIL_STD_461',
    name: 'MIL-STD-461',
    description: 'Requirements for EMI/EMC',
    branches: [],
  },
  {
    catalog_id: 'MIL_STD_1553',
    name: 'MIL-STD-1553',
    description: 'Aircraft internal time division multiplexed data bus',
    branches: ['USAF', 'USN'],
  },
  {
    catalog_id: 'DO178C',
    name: 'DO-178C',
    description: 'Software Considerations in Airborne Systems and Equipment Certification',
    branches: ['USAF', 'USN', 'USSF'],
  },
  {
    catalog_id: 'DO297',
    name: 'DO-297',
    description: 'Integrated Modular Avionics (IMA) Development Guidance',
    branches: ['USAF', 'USN'],
  },
  {
    catalog_id: 'IEEE_STD_829',
    name: 'IEEE Std 829',
    description: 'Standard for Software and System Test Documentation',
    branches: [],
  },
  {
    catalog_id: 'POSIX',
    name: 'POSIX (IEEE 1003)',
    description: 'Portable Operating System Interface standard',
    branches: [],
  },
  {
    catalog_id: 'AUTOSAR',
    name: 'AUTOSAR',
    description: 'Automotive open system architecture',
    branches: ['ARMY'],
  },
  {
    catalog_id: 'OMS_MP',
    name: 'OMS/MP',
    description: 'Open Mission Systems / Universal Command and Control Interface',
    branches: ['USAF', 'USN'],
  },
  {
    catalog_id: 'JAUS',
    name: 'JAUS (SAE AS5684)',
    description: 'Joint Architecture for Unmanned Systems',
    branches: ['ARMY', 'USN'],
  },
  {
    catalog_id: 'IEC_61508',
    name: 'IEC 61508',
    description: 'Functional Safety of Electrical/Electronic/Programmable Systems',
    branches: [],
  },
  {
    catalog_id: 'NATO_STANAG_4586',
    name: 'STANAG 4586',
    description: 'NATO standard for unmanned control system interoperability',
    branches: [],
  },
  {
    catalog_id: 'OpenDDS',
    name: 'DDS (OMG)',
    description: 'Data Distribution Service — real-time pub/sub middleware',
    branches: [],
  },
  {
    catalog_id: 'REST_HTTP',
    name: 'REST/HTTP APIs',
    description: 'Modern web-based interoperability for non-safety-critical interfaces',
    branches: [],
  },
]
