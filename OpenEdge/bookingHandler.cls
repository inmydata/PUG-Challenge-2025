 
/*------------------------------------------------------------------------
   File        : bookingHandler
   Purpose     : Provides endpoints to get and save booking details
   Syntax      : 
   Description : 
   Author(s)   : nick
   Created     : Mon Oct 13 15:39:28 UTC 2025
   Notes       : 
 ----------------------------------------------------------------------*/

USING Progress.Lang.*.
USING OpenEdge.Web.WebResponseWriter.
USING OpenEdge.Net.HTTP.StatusCodeEnum.
USING OpenEdge.Web.WebHandler.
USING Progress.Json.ObjectModel.JsonObject.

BLOCK-LEVEL ON ERROR UNDO, THROW.

CLASS bookingHandler INHERITS WebHandler: 
    
    METHOD OVERRIDE PROTECTED INTEGER HandleNotAllowedMethod( INPUT poRequest AS OpenEdge.Web.IWebRequest ):
        
        UNDO, THROW NEW Progress.Lang.AppError("METHOD NOT IMPLEMENTED").

    END METHOD.

    METHOD OVERRIDE PROTECTED INTEGER HandleNotImplemented( INPUT poRequest AS OpenEdge.Web.IWebRequest ):
        
        UNDO, THROW NEW Progress.Lang.AppError("METHOD NOT IMPLEMENTED").

    END METHOD.

    
    
    /*------------------------------------------------------------------------------
            Purpose: Default handler for the HTTP GET method. Handles both getbooking
                     and getnextavailable booking requests.  
                     
                     Requests to get the next available booking should be:
                     http://<host>[:port]/AgentTools/web/booking/next?startDate=[DATE]
                     
                     Requests to get a booking record should be:
                     http://<host>[:port]/AgentTools/web/booking/getbooking?reg=[REG]
                     
                     The request being 
                     serviced and an optional status code is returned. A zero or 
                     null value means this method will deal with all errors.                                                               
            
            Notes:   Dates will be passed as a string in the format DD-MM-YYYY                                                                     
    ------------------------------------------------------------------------------*/
    METHOD OVERRIDE PROTECTED INTEGER HandleGet( INPUT poRequest AS OpenEdge.Web.IWebRequest ):
        DEFINE VARIABLE oResponse  AS OpenEdge.Net.HTTP.IHttpResponse NO-UNDO.
        DEFINE VARIABLE oWriter    AS OpenEdge.Web.WebResponseWriter  NO-UNDO.
        DEFINE VARIABLE oBody      AS OpenEdge.Core.String            NO-UNDO.
        DEFINE VARIABLE bBooking   AS HANDLE                          NO-UNDO.
        DEFINE VARIABLE jsonOD     AS JsonObject                      NO-UNDO.
        DEFINE VARIABLE lcjsonOD   AS LONGCHAR                        NO-UNDO.        
        DEFINE VARIABLE cQryString AS CHARACTER                       NO-UNDO.
        DEFINE VARIABLE cPair      AS CHARACTER                       NO-UNDO.
        DEFINE VARIABLE ix         AS INTEGER                         NO-UNDO.
        DEFINE VARIABLE cReg       AS CHARACTER                       NO-UNDO INITIAL ?.
        DEFINE VARIABLE startDate  AS CHARACTER                       NO-UNDO.
        DEFINE VARIABLE dDate      AS DATE                            NO-UNDO.
        DEFINE VARIABLE bFound     AS LOGICAL                         NO-UNDO.
        
        /* Parse any query parameters */
        cQryString = STRING(poRequest:GetContextValue("QUERY_STRING")).
        REPEAT ix = 1 TO NUM-ENTRIES(cQryString,'&'):
            cPair = ENTRY(ix,cQryString,'&').
            IF ENTRY(1,cPair,'=') = "reg" THEN cReg = ENTRY(2,cPair,'=').
            IF ENTRY(1,cPair,'=') = "startDate" THEN DO:
                startDate = ENTRY(2,cPair,'=').
            END.
        END.
        
        /* Create a response object */
        ASSIGN oResponse = NEW OpenEdge.Web.WebResponse().
        
        /* Parse the path parameter */
        /* Are we are looking for the next available date, or looking up a booking? */
        DEFINE VARIABLE cProcess AS CHARACTER NO-UNDO.
        cProcess = poRequest:GetPathParameter("FINAL_MATCH_GROUP").
        
        /* Process next available booking date request */
        IF cProcess = "/next" THEN DO:
            
            /* Parse the start date from string extracted from the query parameter. If not present, default to today */
            IF startDate <> ? OR startDate <> "" 
                THEN dDate = DATE(
                    INTEGER(ENTRY(2, startDate, "-")),  /* month */
                    INTEGER(ENTRY(1, startDate, "-")),   /* day */
                    INTEGER(ENTRY(3, startDate, "-"))  /* year */
                    ) + 1.
                ELSE dDate = TODAY + 1.
                
            /* Find the next available booking date after start date */    
            bFound = FALSE.    
            DO WHILE NOT bFound:
                IF WEEKDAY(dDate) >= 2 AND WEEKDAY(dDate) <= 6 AND NOT CAN-FIND(Booking WHERE Booking.BookingDate = dDate) THEN bFound = TRUE. 
                ELSE dDate = dDate + 1.   
            END.
        
            /* Add json to the response that contains the booking date */
            jsonOD = NEW JsonObject().
            jsonOD:Add("BookingDate", STRING(DAY(dDate), "99") + "-" +
                STRING(MONTH(dDate), "99") + "-" +
                STRING(YEAR(dDate), "9999")).
            lcjsonOD = jsonOD:GetJsonText().
            oBody = NEW OpenEdge.Core.String(lcjsonOD).
            /* Set the response code to OK, and content type to json */
            oResponse:StatusCode = INTEGER(StatusCodeEnum:OK).
            oResponse:ContentType   = 'text/json':u.
        END.
        
        /* Process get booking request */
        ELSE IF cProcess = "/getbooking" THEN DO:
            /* Find the booking */
            FIND FIRST Booking WHERE Booking.reg = cReg NO-LOCK NO-ERROR.
            /* If the booking is found, add the details as a json object to the response body */
            IF AVAILABLE Booking THEN DO:
                jsonOD = NEW JsonObject().
                jsonOD:Add("BookingDate", STRING(DAY(Booking.BookingDate), "99") + "-" + STRING(MONTH(Booking.BookingDate), "99") + "-" + STRING(YEAR(Booking.BookingDate), "9999")).
                jsonOD:ADD("Description", Booking.Description).
                lcjsonOD = jsonOD:GetJsonText().
                oBody = NEW OpenEdge.Core.String(lcjsonOD).
                /* Set the response code to OK, and content type to json */
                oResponse:StatusCode = INTEGER(StatusCodeEnum:OK).
                oResponse:ContentType   = 'text/json':u.
            END.
            
            /* We didn't find a booking. Respond with an appropriate error and no content response code */
            ELSE DO:
                IF cReg = "" OR cReg = ? THEN oBody = NEW OpenEdge.Core.String('You must provide a reg to look up a booking').
                ELSE oBody = NEW OpenEdge.Core.String('Booking for car with reg ' + cReg + ' not found').
                oResponse:StatusCode = INTEGER(StatusCodeEnum:NoContent).
                oResponse:ContentType   = 'text/text':u.
            END.
        END.
        
        /* The path variable indicating whether we are getting a booking or next available date was missing */
        /* Respond with an appropriate error and not found response code */
        ELSE DO:
            oBody = NEW OpenEdge.Core.String('Invalid Path').
            oResponse:StatusCode = INTEGER(StatusCodeEnum:NotFound).
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
           Purpose: Default Post Handler to save a new booking record.                                                               
           Notes:                                                                        
   ------------------------------------------------------------------------------*/
    METHOD OVERRIDE PROTECTED INTEGER HandlePost( INPUT poRequest AS OpenEdge.Web.IWebRequest ):
        DEFINE VARIABLE dBookingDate    AS DATE                             NO-UNDO.
        DEFINE VARIABLE oResponse       AS OpenEdge.Net.HTTP.IHttpResponse  NO-UNDO.
        DEFINE VARIABLE oWriter         AS OpenEdge.Web.WebResponseWriter   NO-UNDO.
        DEFINE VARIABLE oBody           AS OpenEdge.Core.String             NO-UNDO.
        DEFINE VARIABLE cReg            AS CHARACTER                        NO-UNDO.
        DEFINE VARIABLE cBookingDate    AS CHARACTER                        NO-UNDO.
        DEFINE VARIABLE cDescription    AS CHARACTER                        NO-UNDO.
        DEFINE VARIABLE oJson           AS JsonObject                       NO-UNDO.
        
        /* Extract the booking details from the body */
        oJson = CAST(poRequest:Entity, JsonObject).
        ASSIGN 
            cReg         = oJson:GetCharacter("reg")
            cBookingDate = oJson:GetCharacter("date")
            cDescription = oJson:GetCharacter("description").
        dBookingDate = DATE(
            INTEGER(ENTRY(2, cBookingDate, "-")),  /* month */
            INTEGER(ENTRY(1, cBookingDate, "-")),  /* day */
            INTEGER(ENTRY(3, cBookingDate, "-"))   /* year */
        ).  
        
        /* Create a response object */
        ASSIGN oResponse = NEW OpenEdge.Web.WebResponse().
        
        /* If a booking is already present for this date, return appropriate error and conflict response code */
        IF CAN-FIND(Booking WHERE Booking.BookingDate = dBookingDate) THEN DO:
            oBody = NEW OpenEdge.Core.String("A booking for the date " + STRING(dBookingDate) + " already exists").
            oResponse:StatusCode = INTEGER(StatusCodeEnum:Conflict).
        END.
        
        /* Create a booking record, and return OK message with OK response code */
        ELSE DO TRANSACTION:
            CREATE Booking.
            ASSIGN 
                Booking.reg         = cReg
                Booking.BookingDate = dBookingDate
                Booking.Description = cDescription.
            RELEASE Booking.
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