# UnderControl

**Agentic AI for Project Diagnosis & Recovery**

UnderControl is an AI-powered project analysis and recovery system designed to help project managers understand delayed software projects and evaluate possible recovery actions before changing the real project plan.

## Problem

Project data can contain hundreds of tasks, statuses, priorities, owners, timelines, and dependencies. Finding the actual causes of delays manually can be time-consuming, while traditional dashboards mainly show what happened without testing possible recovery actions.

## Solution

UnderControl takes a project export, analyzes its current state, identifies important issues and bottlenecks, and simulates candidate recovery actions. The system then produces structured recovery guidance based on the analysis and simulation results.

## How It Works

**1. Upload Project**
Upload a Jira project CSV.

**2. Diagnose**
Analyze the project state, root causes, bottlenecks, dependencies, and schedule signals.

**3. Test Recovery Actions**
Simulate possible interventions such as resource reassignment, reprioritization, or dependency resolution.

**4. Generate Recovery Plan**
Provide structured recovery guidance based on the available evidence and simulation results.

## Technologies

* Python
* LangChain
* LLMs
* RAG
* ChromaDB
* Sentence Transformers
* Pandas
* Streamlit

## Data & Evidence

The system uses current project data through **Live RAG** and historical Jira cases through **Ground Truth RAG** to provide additional context.

## Project Status

This project is developed as a multi-agent system for project diagnosis and recovery. The current implementation focuses on project analysis, evidence retrieval, and recovery simulation.

## Team Members

* **Aryaf Alotaibi**
* **Ruba Alitri**
* **Shams Alarifi**
* **Enas Alruhali**
* **Lana  Aldeaiji**

## Run locally

    pip install -r requirements.txt
    streamlit run app.py
