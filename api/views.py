import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .services.factory import CloudServiceFactory
from .parsers.sms_xml import parse_sms_xml

logger = logging.getLogger(__name__)

@api_view(['GET'])
def get_latest_sms(request):
    """Fetch the latest SMS backup for a given provider."""
    provider = request.query_params.get('provider')
    
    if not provider:
        return Response(
            {'error': 'Provider parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Create the service using the CloudServiceFactory
        service = CloudServiceFactory.create(provider)
        
        if not service:
            raise ValueError(f"Invalid provider: {provider}")

        # Get the latest SMS backup from the cloud service
        xml_content = service.get_latest_sms_backup()

        # If no content is returned, handle the case
        if not xml_content:
            raise ValueError("No SMS backup found.")

        # Parse the XML content into structured SMS data
        sms_data = parse_sms_xml(xml_content)

        return Response({'sms_messages': sms_data}, status=status.HTTP_200_OK)
    
    except ValueError as ve:
        # Catch specific validation errors (invalid provider, no data)
        logger.error(f"Validation error: {ve}")
        return Response({'error': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error: {e}")
        return Response(
            {'error': 'An unexpected error occurred. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
