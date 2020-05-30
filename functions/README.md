# Azure Functions

The `detect-objects` function is a blob-triggered function that executes on any write to the connected Azure blob storage account.  

When an image is written to the blob container, the function sends the image to a Custom Vision object detection model to get bounding box predictions. The detected regions are then extracted (cropped) from the original image and sent to the Cognitive Services Computer Vision API to get the dominant color.  

### Writing results
A comment indicating a placeholder for writing these results to your datastore is written in the entry script: `__init__.py`.  

You can set up an output binding to an Azure Function to easily write results to a datastore.  The supported bindings can be found here: [Azure Functions supported bindings](https://docs.microsoft.com/en-us/azure/azure-functions/functions-triggers-bindings#supported-bindings).  

To write to datastores that are not supported, you can use the relevant APIs.  For example, to write to an Azure PostgreSQL database, see the [Azure Database for PostgreSQL REST API Reference](https://docs.microsoft.com/en-us/rest/api/postgresql/)

### Developing and publishing Azure Functions

This folder contains the required files to deploy the Function to Azure.  In addition to the files, all environment variables indicated within `__init__.py` must be set in your Azure Function's Application Settings within the Azure Portal.

For reference on building and deploying Azure Functions using VS Code, see [this documentation](https://docs.microsoft.com/en-us/azure/azure-functions/functions-develop-vs-code).
