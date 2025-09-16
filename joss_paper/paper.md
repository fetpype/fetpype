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
date: 19 June 2025
bibliography: paper.bib
---

# Summary

Fetal brain Magnetic Resonance Imaging (MRI) is crucial for assessing neurodevelopment *in utero*. However, analyzing this data presents significant challenges due to fetal motion, low signal-to-noise ratio, and the need for complex multi-step processing, including motion correction, super-resolution reconstruction, and segmentation. While various specialized tools exist for individual steps, integrating them into robust, reproducible, and user-friendly workflows that go from raw image to volume and surface analysis is not straightforward. This lack of standardization hinders reproducibility across studies and limits the adoption of advanced analysis techniques for researchers and clinicians. To address these challenges, we introduce `Fetpype`, an open-source Python library designed to streamline and standardize the preprocessing and analysis of T2-weighted fetal brain MRI data as illustrated in (\autoref{fig:fetpype}).

# Statement of need

`Fetpype` is a Python package integrating several established neuroimaging software principles and tools to create a cohesive and extensible framework, which we summarize in four points. 

1. **Data Standardization**: `Fetpype` expects input data organized according to the Brain Imaging Data Structure (BIDS) standard [@gorgolewski2016brain], promoting interoperability and simplifying data management. 
2. **Containerization**: Individual processing tools are encapsulated within Docker or Singularity containers. This ensures reproducibility and reduces installation issues, providing a better experience for the end user. 
3. **Workflow Management**: The `Nipype` library [@gorgolewski2011nipype] is used to construct processing workflows: it provides a robust interface for combining different steps from different containers or packages, facilitating data caching and parallelization, and allowing pipelines to be easily shareable. 
4. **Configuration**: Pipeline configuration is managed using simple YAML files and the Hydra library [@Yadan2019Hydra], allowing users to easily select between different modules or parameters without directly modifying the code. The current implementation of Fetpype integrates modules for **data preprocessing**, **super-resolution reconstruction** (NeSVoR [@xu2023nesvor], SVRTK [@kuklisova-murgasova_reconstruction_2012; @uus2022automated], or NiftyMIC [@ebner2020automated]), **segmentation** (BOUNTI [@uus2023bounti] or the developing human connectome project pipeline [@makropoulos2018developing]) and **cortical surface extraction** (using a custom implementation available at https://github.com/fetpype/surface_processing based on [@bazin2005topology; @bazin2007topology; @ma2022cortexode]).

The objective underlying the conceptualization of 'Fetpype' was to provide the fetal MRI community with a standardized, reproducible, and flexible open-source platform for preprocessing and analysis. We believe this tool can facilitate research and improve the comparability across studies. We also intend to foster collaboration across research teams by providing Fetpype as a central framework that facilitates the dissemination of new image processing methods for clinical applications. The pipeline is publicly available on GitHub (https://github.com/fetpype/fetpype), and its open-source nature and modular design facilitate community involvement: researchers can integrate their own tools by creating corresponding `Nipype` interfaces and container wrappers, following the package contribution guidelines.

In the future, we plan to supplement `Fetpype` with an automated reporting library containing automated quality control [@sanchez2024fetmrqc; @sanchez2025automatic], subject-wise and population-wise biometry and volumetry [@esteban2017mriqc], as well as spectral analysis [@germanaud2012larger]. We welcome contributions of authors desiring to integrate their method to `Fetpype`. 

![The different steps covered by `Fetpype`. Starting from several T2-weighted stacks of thick slices of the fetal brain (_acquisition_), `Fetpype` pre-processes data before feeding them to a _super-resolution reconstruction_ algorithm that fuses them in a single high-resolution volume. This volume then underegoes _segmentation_, before moving to cortical _surface extraction_. \label{fig:fetpype}](fetpype.png)

# Acknowledgements
This work was funded by Era-net NEURON MULTIFACT project (TS: Swiss National Science Foundation grants 31NE30_203977, 215641; GA: French National Research Agency, Grant ANR-21-NEU2-0005; GMJ, GP:  Ministry of Science, Innovation and Universities: MCIN/AEI/10.13039/501100011033/), and the SulcalGRIDS Project, (GA: French National Research Agency Grant ANR-19-CE45-0014).  We acknowledge the CIBM Center for Biomedical Imaging, a Swiss research center of excellence founded and supported by CHUV, UNIL, EPFL, UNIGE and HUG. This research was also supported by grants from NVIDIA and utilized NVIDIA RTX6000 ADA GPUs.


# References