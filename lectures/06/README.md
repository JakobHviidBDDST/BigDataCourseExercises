# Lecture 6 - Architecture Exercise 1

This weeks exercise is an Architecture Exercise where you will combine knowledge from multiple lectures to help a company with their Big Data needs.

You will be giving a group presentation on your design proposal.

## Twitter Analysis Case
Company X is creating a sentiment analysis tools for political candidates to evaluate the publics reaction to political statements, but needs help designing the architecture of their system. You have been hired as a consultant to help with this task.

The analysis tool analyses the unstructured sentences, but also uses the metadata added by Twitter.

### The solution Requirements
- Ingest live data and react to live events happening so they can measure reactions when a press briefing is happening.
- Automatically connect to their clients database holding events, schedules, and more. This data needs to be correlated with the ML model of the analysis tool to function as intended, and is also needed for historical analysis.
- The analysis tool is trained on historical data, so there needs to be designed a solution for re-training the ML model, and let it take over the current running live model.
- A frontend needs to be available to handle live events and updates as new data is analyzed.

### Remember to
- Identify bottlenecks
- Address data format
- Address deployment platform
- Address data flow
- Address how data is analyzed
- Address how the frontend gets data
- Address how the platform is hostede (Hardware, Cloud, etc.)

**Remember, diagrams are your most valuable tools to communicate your architecture!**
