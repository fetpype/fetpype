---
title: 'Fetpype: An Open-Source Pipeline for Reproducible Fetal Brain MRI Analysis'
tags:
  - Python
  - fetal brain MRI
  - super-resolution reconstruction
  - segmentation
  - surface extraction
authors:
  - name: Thomas Sanchez
    orcid: 0000-0003-3668-5155
    equal-contrib: true
    affiliation: "1, 2" # (Multiple affiliations must be quoted)
    corredponsing: true
  - name: Gerard Martí-Juan
    orcid: 0000-0003-4729-7182
    equal-contrib: true
    affiliation: 3 # (Multiple affiliations must be quoted)
  - name: David Meunier
    orcid: 0000-0002-5812-6138
    affiliation: 4
  - name: Miguel Angel Gonzalez Ballester
    orcid: 0000-0002-9227-6826
    affiliation: "3, 5" # (Multiple affiliations must be quoted)
  - name: Oscar Camara
    orcid: 0000-0002-5125-6132
    affiliation: 3 # (Multiple affiliations must be quoted)
  - name: Elisenda Eixarch 
    orcid: 0000-0001-7379-9608
    affiliation: "6, 7" # (Multiple affiliations must be quoted)
  - name: Gemma Piella
    orcid: 0000-0001-5236-5819
    affiliation: 3
  - name: Meritxell Bach Cuadra
    orcid: 0000-0003-2730-4285
    affiliation: "1, 2"
  - name: Guillaume Auzias
    orcid: 0000-0002-0414-5691
    affiliation: 4
affiliations:
 - name: CIBM – Center for Biomedical Imaging, Switzerland
   index: 1
 - name: Department of Diagnostic and Interventional Radiology, Lausanne University Hospital and University of Lausanne, Switzerland
   index: 2
 - name: BCN MedTech, Department of Engineering, Universitat Pompeu Fabra, Spain
   index: 3
 - name: Aix-Marseille Université, CNRS, Institut de Neurosciences de La Timone, France
   index: 4
 - name: ICREA, Barcelona, Spain
   index: 5
 - name: BCNatal | Fetal Medicine Research Center (Hospital Clínic and Hospital Sant Joan de Déu, Universitat de Barcelona), Barcelona, Spain
   index: 6
 - name: Institut d’Investigacions Biomèdiques August Pi i Sunyer (IDIBAPS), Barcelona, Spain and Centre for Biomedical Research on Rare Diseases (CIBERER), Barcelona, Spain
   index: 7
date: 22 January 2026
bibliography: paper.bib
---


# Summary

Fetal brain magnetic resonance imaging (MRI) is crucial for assessing neurodevelopment *in utero*. However, fetal MRI analysis remains technically challenging due to fetal motion, low signal-to-noise ratio, and the need for complex multi-step processing pipelines. These pipelines typically include motion correction, super-resolution reconstruction, tissue segmentation, and cortical surface extraction. While specialized tools exist for each individual processing step, integrating them into a robust, reproducible, and user-friendly end-to-end workflow remains difficult. This fragmentation limits reproducibility across studies and hinders the adoption of advanced fetal neuroimaging methods in both research and clinical contexts.

`Fetpype` addresses this gap by providing a standardized, modular, and reproducible framework for fetal brain MRI preprocessing and analysis, enabling researchers to process raw T2-weighted acquisitions through to derived volumetric and surface-based outputs within a unified workflow.

# Statement of need
`Fetpype` is an open-source Python package designed to streamline and standardize the preprocessing and analysis of T2-weighted fetal brain MRI data. The package targets the fetal neuroimaging community, where methodological heterogeneity and complex software dependencies have historically limited reproducibility and comparability across studies.

Existing fetal brain MRI tools typically focus on individual processing steps and require customized code for pre- and post-processing, as well as to connect different modules, making it difficult to reproduce processing results across studies. `Fetpype` addresses these challenges by providing a configurable, containerized, and `Nipype`-driven solution that integrates state-of-the-art fetal MRI processing tools into a cohesive pipeline. By emphasizing reproducibility, extensibility, and ease of use, `Fetpype` lowers the barrier to applying advanced fetal MRI analysis methods and facilitates consistent processing across sites, scanners, and studies.  In doing so, `Fetpype` improves comparability across studies and supports community collaboration by facilitating the dissemination of new image processing methods for clinical applications. The pipeline is publicly available on GitHub (https://github.com/fetpype/fetpype).

![The different steps covered by `Fetpype`. Starting from several T2-weighted stacks of thick slices of the fetal brain (_acquisition_), `Fetpype` pre-processes data before feeding them to a _super-resolution reconstruction_ algorithm that fuses them in a single high-resolution volume. This volume then undergoes _segmentation_, before moving to cortical _surface extraction_. \label{fig:fetpype}](fetpype.png)

# Software design
`Fetpype` is built around four core design principles: data standardization, containerization, workflow orchestration, and flexible configuration:

1. **Data Standardization**: `Fetpype` expects input data organized according to the Brain Imaging Data Structure (BIDS) standard [@gorgolewski2016brain], promoting interoperability and simplifying data management. 
2. **Containerization**: Individual processing tools are encapsulated within Docker or Singularity containers. This ensures reproducibility and reduces installation issues, providing a better experience for the end user. 
3. **Workflow Management**: The `Nipype` library [@gorgolewski2011nipype] is used to construct processing workflows: it provides a robust interface for combining different steps from different containers or packages, facilitating data caching and parallelization, and allowing pipelines to be easily shareable. 
4. **Configuration**: Pipeline configuration is managed using simple YAML files and the Hydra library [@Yadan2019Hydra], allowing users to easily select between different modules or parameters without directly modifying the code. The current implementation of `Fetpype` integrates modules for:
    a. **Data preprocessing**: including brain extraction using `Fetal-BET` [@faghihpirayesh2024fetal], non-local means denoising [@manjon2010adaptive] and N4 bias-field correction [@tustison2010n4itk], all wrapped into a single container built at https://github.com/fetpype/utils_container, 
    b. **Super-resolution reconstruction**: implementing three widely used pipelines: NeSVoR [@xu2023nesvor], SVRTK [@kuklisova-murgasova_reconstruction_2012; @uus2022automated], and NiftyMIC [@ebner2020automated], 
    c. **Segmentation**: implementing BOUNTI [@uus2023bounti] and the developing human connectome project pipeline [@makropoulos2018developing] and 
    d. **Cortical surface extraction**: using a custom implementation available at https://github.com/fetpype/surface_processing based on [@bazin2005topology; @bazin2007topology; @ma2022cortexode].
  
The overall processing workflow is summarized in \autoref{fig:fetpype}.



# Research impact statement
`Fetpype` is the result of a longstanding collaboration within a European consortium of researchers specializing in fetal neuroimaging. Its default configurations and processing workflows have been the result of extensive testing to achieve robust processing on data acquired across multiple hospitals in France, Spain, and Switzerland, covering a range of scanners and acquisition protocols.

The framework has been used to process large-scale fetal MRI datasets within the consortium, has contributed to a first publication (citation pending), and is supporting ongoing research projects. Fetpype is used by multiple research groups and has begun to receive external contributions, including pull requests that integrate additional processing methods. This suggests that `Fetpype` addresses a clear methodological need and can serve as shared community infrastructure for fetal brain MRI research.


In the future, we plan to supplement `Fetpype` with an automated reporting library containing automated quality control [@sanchez2024fetmrqc; @sanchez2025automatic], subject-wise and population-wise biometry and volumetry [@esteban2017mriqc; @neves2025scanner], as well as spectral analysis of surfaces [@germanaud2012larger]. We welcome community contributions, particularly implementations of new methods that can be integrated into the existing containerized workflow framework.



# AI usage disclosure
GitHub Copilot, integrated within Visual Studio Code, was used during software development to assist with code completion and implementation. ChatGPT (GPT-5.2) was used for proofreading and language refinement of the manuscript. The authors take full responsibility for the written content.


# Acknowledgements
This work was funded by Era-net NEURON MULTIFACT project (TS: Swiss National Science Foundation grants 31NE30_203977, 215641; GA: French National Research Agency, Grant ANR-21-NEU2-0005; EE: Instituto de Salud Carlos III (ISCIII) grant AC21\_2/00016; GMJ, GP, OC, MAGB:  Ministry of Science, Innovation and Universities: MCIN/AEI/10.13039/501100011033/), the SulcalGRIDS Project, (GA: French National Research Agency Grant ANR-19-CE45-0014), the pediatric domain shifts project (TS: SNSF 205320-215641), and NVIDIA research grants with the use of NVIDIA RTX6000 ADA GPUs.  We acknowledge the CIBM Center for Biomedical Imaging, a Swiss research center of excellence founded and supported by CHUV, UNIL, EPFL, UNIGE and HUG.


# References
