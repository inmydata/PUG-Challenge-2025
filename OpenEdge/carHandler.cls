 
/*------------------------------------------------------------------------
   File        : carHandler
   Purpose     : Provides endpoints to get and save car details
   Syntax      : 
   Description : 
   Author(s)   : nick
   Created     : Mon Oct 13 12:37:40 UTC 2025
   Notes       : 
 ----------------------------------------------------------------------*/

USING Progress.Lang.*.
USING OpenEdge.Web.WebResponseWriter.
USING OpenEdge.Net.HTTP.StatusCodeEnum.
USING OpenEdge.Web.WebHandler.
USING Progress.Json.ObjectModel.JsonObject.

BLOCK-LEVEL ON ERROR UNDO, THROW.

CLASS carHandler INHERITS WebHandler: 

    DEFINE TEMP-TABLE ttCar LIKE Car. 
		
    /*------------------------------------------------------------------------------
            Purpose: Handler for unsupported methods. The request being serviced and
                     an optional status code is returned. A zero or null value means 
                     this method will deal with all errors.                                                               
            Notes:                                                                        
    ------------------------------------------------------------------------------*/
    METHOD OVERRIDE PROTECTED INTEGER HandleNotAllowedMethod( INPUT poRequest AS OpenEdge.Web.IWebRequest ):
	
        /* Throwing an error from this method results in a 500/Internal Server Error response. 
        The web handler will attempt to log this exception.
 	    
        See the HandleGet method's comments on choosing a value to return from this method. */
        	
        UNDO, THROW NEW Progress.Lang.AppError("METHOD NOT IMPLEMENTED").
    END METHOD.


    /*------------------------------------------------------------------------------
            Purpose: Handler for unknown methods. The request being serviced and an 
                     optional status code is returned. A zero or null value means 
                     this method will deal with all errors.                                                               
            Notes:                                                                        
    ------------------------------------------------------------------------------*/
    METHOD OVERRIDE PROTECTED INTEGER HandleNotImplemented( INPUT poRequest AS OpenEdge.Web.IWebRequest ):
	
        /* Throwing an error from this method results in a 500/Internal Server Error response. 
        The web handler will attempt to log this exception.
 	    
        See the HandleGet method's comments on choosing a value to return from this method. */	
        UNDO, THROW NEW Progress.Lang.AppError("METHOD NOT IMPLEMENTED").
    END METHOD.
 	
	
    /*------------------------------------------------------------------------------
            Purpose: Default handler for the HTTP GET method to return a car record. 
                     The request being serviced and an optional status code is returned. 
                     A zero or null value means this method will deal with all errors.                                                               
            Notes:                                                                        
    ------------------------------------------------------------------------------*/
    METHOD OVERRIDE PROTECTED INTEGER HandleGet( INPUT poRequest AS OpenEdge.Web.IWebRequest ):
        DEFINE VARIABLE oResponse  AS OpenEdge.Net.HTTP.IHttpResponse NO-UNDO.
        DEFINE VARIABLE oWriter    AS OpenEdge.Web.WebResponseWriter  NO-UNDO.
        DEFINE VARIABLE oBody      AS OpenEdge.Core.String            NO-UNDO.
        DEFINE VARIABLE bCar       AS HANDLE                          NO-UNDO.
        DEFINE VARIABLE jsonOD     AS JsonObject                      NO-UNDO.
        DEFINE VARIABLE lcjsonOD   AS LONGCHAR                        NO-UNDO.        
        DEFINE VARIABLE cQryString AS CHARACTER                       NO-UNDO.
        DEFINE VARIABLE cPair      AS CHARACTER                       NO-UNDO.
        DEFINE VARIABLE ix         AS INTEGER                         NO-UNDO.
        DEFINE VARIABLE cReg       AS CHARACTER                       NO-UNDO INITIAL ?.
        
        /* First, extract the car reg from the query parameters */
        cQryString = STRING(poRequest:GetContextValue("QUERY_STRING")).
        REPEAT ix = 1 TO NUM-ENTRIES(cQryString,'&'):
            cPair = ENTRY(ix,cQryString,'&').
            IF ENTRY(1,cPair,'=') = "reg" THEN cReg = ENTRY(2,cPair,'=').
        END.
        
        /* Create a response object */
        ASSIGN oResponse = NEW OpenEdge.Web.WebResponse().
        
        /* Make sure we only pass back trhe current car */
        EMPTY TEMP-TABLE ttCar.
        bCar = TEMP-TABLE ttCar:DEFAULT-BUFFER-HANDLE.
        FIND FIRST Car WHERE Car.reg = cReg NO-LOCK NO-ERROR.
        
        /* If we've found the car, build a json response from our temp-table */
        IF AVAILABLE Car THEN DO:
            CREATE ttCar.
            BUFFER-COPY Car TO ttCar.
            jsonOD = NEW JsonObject().
            jsonOD:Read(bCar).    
            lcjsonOD = jsonOD:GetJsonText().
            oBody = NEW OpenEdge.Core.String(lcjsonOD).
            oResponse:StatusCode = INTEGER(StatusCodeEnum:OK).
            /* HTTP messages require a content type */
            oResponse:ContentType   = 'text/text':u.
        END.
        
        /* Couldn't find the car, so pass back an appropriate message and no content response */
        ELSE DO:
            oBody = NEW OpenEdge.Core.String('Car with reg ' + cReg + ' not found').
            oResponse:StatusCode = INTEGER(StatusCodeEnum:NoContent).
            /* HTTP messages require a content type */
            oResponse:ContentType   = 'text/text':u.
        END.
        
        /* Assign body to the response, and good practice to also give length */
        ASSIGN 
            oResponse:Entity        = oBody
            oResponse:ContentLength = oBody:Size.
        
        /* The WebResponseWriter ensures that the status line and
           all headers are written out before the message body/entity. */
        ASSIGN 
            oWriter = NEW WebResponseWriter(oResponse).
        oWriter:Open().
        /* Finish writing the response message */
        oWriter:Close().
        /* A response of 0 means that this handler will build the entire response;
           a non-zero value is mapped to a static handler in the webapp's /static/error folder.
           The mappings are maintained in the webapps's WEB-INF/web.xml 
           A predefined set of HTTP status codes is provided in the OpenEdge.Net.HTTP.StatusCodeEnum 
           enumeration */
        RETURN 0.
		
    END METHOD. 
 	  
    /*------------------------------------------------------------------------------
            Purpose: Default Post Handler to save a new car record.                                                                
            Notes:                                                                        
    ------------------------------------------------------------------------------*/
    METHOD OVERRIDE PROTECTED INTEGER HandlePost( INPUT poRequest AS OpenEdge.Web.IWebRequest ):
        DEFINE VARIABLE oResponse   AS OpenEdge.Net.HTTP.IHttpResponse  NO-UNDO.
        DEFINE VARIABLE oWriter     AS OpenEdge.Web.WebResponseWriter   NO-UNDO.
        DEFINE VARIABLE oBody       AS OpenEdge.Core.String             NO-UNDO.
        DEFINE VARIABLE cReg        AS CHARACTER                        NO-UNDO.
        DEFINE VARIABLE cMake       AS CHARACTER                        NO-UNDO.
        DEFINE VARIABLE cModel      AS CHARACTER                        NO-UNDO.
        DEFINE VARIABLE cYear       AS CHARACTER                        NO-UNDO.
        DEFINE VARIABLE oJson       AS JsonObject                       NO-UNDO.
        
        /* Extract the car details from the body */
        oJson = CAST(poRequest:Entity, JsonObject).
        ASSIGN 
            cReg   = oJson:GetCharacter("reg")
            cMake  = oJson:GetCharacter("make")
            cModel = oJson:GetCharacter("model")
            cYear  = oJson:GetCharacter("year").
                
        /* Create a response object */
        ASSIGN oResponse = NEW OpenEdge.Web.WebResponse().
        
        /* Cannot create a car record without a reg value, so pass back bad request with a sensible error message */
        IF cReg = ? OR cReg = "" THEN DO:
            oBody = NEW OpenEdge.Core.String('You must provide a reg value to create a car').
            oResponse:StatusCode = INTEGER(StatusCodeEnum:BadRequest).
        END.
        
        /* Cannot create a car record with a duplicate reg value, so pass back conflict with a sensible error message */
        ELSE IF CAN-FIND(FIRST Car WHERE Car.reg = cReg) THEN DO:
            oBody = NEW OpenEdge.Core.String('Car with reg ' + cReg + ' already exists').
            oResponse:StatusCode = INTEGER(StatusCodeEnum:Conflict).
        END.
        
        /* Create the car record, and pass back OK and OK response code */
        ELSE DO TRANSACTION:
            CREATE Car.
            ASSIGN 
                Car.reg = cReg
                Car.make = cMake
                Car.model = cModel
                Car.year = INTEGER(cYear).
            RELEASE Car.
            oBody = NEW OpenEdge.Core.String("OK").
            oResponse:StatusCode = INTEGER(StatusCodeEnum:OK).
        END.  
        
        /* HTTP messages require a content type */
        oResponse:ContentType   = 'text/text':u. 
        /* Assign body to the response */
        oResponse:Entity        = oBody.
        /* Good practice to also give length */
        oResponse:ContentLength = oBody:Size.
        
        /* The WebResponseWriter ensures that the status line and
           all headers are written out before the message body/entity. */
        oWriter = NEW WebResponseWriter(oResponse).
        oWriter:Open().
        /* Finish writing the response message */
        oWriter:Close().     
    END METHOD.
 	
END CLASS.