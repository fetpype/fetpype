---
title: 'Fetpype: An Open-Source pipeline for reproducible Fetal Brain MRI Analysis'
tags:
  - Python
  - fetal brain MRI
  - super-resolution reconstruction
  - segmentation
authors:
  - name: Thomas Sanchez
    orcid: 0000-0000-0000-0000
    equal-contrib: true
    affiliation: "1, 2" # (Multiple affiliations must be quoted)
    corredponsing: true
  - name: Gerard Martí-Juan
    orcid: 0000-0000-0000-0000
    equal-contrib: true
    affiliation: 3 # (Multiple affiliations must be quoted)
  - name: David Meunier
    affiliation: 4
  - name: Gemma Piella
    affiliation: 3
  - name: Meritxell Bach Cuadra
    affiliation: "1, 2"
  - name: Guillaume Auzias
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

Fetal brain Magnetic Resonance Imaging (MRI) is crucial for assessing neurodevelopment *in utero*. However, analyzing this data presents significant challenges due to fetal motion, low signal-to-noise ratio, and the need for complex multi-step processing, including motion correction, super-resolution reconstruction, and segmentation. While various specialized tools exist for individual steps, integrating them into robust, reproducible, and user-friendly workflows that go from raw image to volume and surface analysis is not straightforward (\autoref{fig:fetpype}). This lack of standardization hinders reproducibility across studies and limits the adoption of advanced analysis techniques for researchers and clinicians. To address these challenges, we introduce `Fetpype`, an open-source Python library designed to streamline and standardize the preprocessing and analysis of fetal brain MRI data.

# Statement of need

`Fetpype` is a Python package integrating several established neuroimaging software principles and tools to create a cohesive and extensible framework, which we summarize in four points. 

1. **Data Standardization**: `Fetpype` expects input data organized according to the Brain Imaging Data Structure (BIDS) standard [@gorgolewski2016brain], promoting interoperability and simplifying data management. 
2. **Containerization**: Individual processing tools are encapsulated within Docker or Singularity containers. This ensures reproducibility and reduces installation issues, providing a better experience for the end user. 
3. **Workflow Management**: The `Nipype` library [@gorgolewski2011nipype] is used to construct processing workflows: it provides a robust interface for combining different steps from different containers or packages, facilitating data caching and parallelization, and allowing pipelines to be easily shareable. 
4. **Configuration**: Pipeline configuration is managed using simple YAML files and the Hydra library [@Yadan2019Hydra], allowing users to easily select between different modules or parameters without directly modifying the code. The current implementation of Fetpype integrates modules for data preprocessing, high resolution reconstruction (NeSVoR [@xu2023nesvor], SVRTK [@kuklisova-murgasova_reconstruction_2012,@uus2022automated], or NiftyMIC [@ebner2020automated]), segmentation (using existing, popular pipelines like BOUNTI [@uus2023bounti] or the developing human connectome project pipeline [@makropoulos2018developing]).

`Fetpype` was designed to be used by the fetal MRI community by providing a standardized, reproducible and flexible open-source platform for preprocessing and analysis. We believe this tool can facilitate research, improve comparability between studies, and foster collaboration. The pipeline is publicly available on GitHub (https://github.com/fetpype/fetpype), and its open-source nature and modular design facilitate community involvement: researchers can integrate their own tools by creating corresponding `Nipype` interfaces and container wrappers, following the package contribution guidelines.

In the future, the package will be extended to feature cortical surface extraction as well as spectral analysis. We welcome contributions of authors wanting to integrate their method to `Fetpype`. 

![The different steps covered by `Fetpype`. The current version of `Fetpype` implements the different processing steps needed to compute clinically relevant measures like biometric, volumetric or surface descriptors, but does not implement them. \label{fig:fetpype}](fetpype.png)

# Acknowledgements
This work was funded by Era-net NEURON MULTIFACT project (TS: Swiss National Science Foundation grant 31NE30_203977; GA: French National Research Agency, Grant ANR-21-NEU2-0005; GM, GP:  Ministry of Science, Innovation and Universities: MCIN/AEI/10.13039/501100011033/), and the SulcalGRIDS Project, (GA: French National Research Agency Grant ANR-19-CE45-0014). 


# References