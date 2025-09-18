@openapi.openedge.export FILE(type="REST", executionMode="singleton", useReturnValue="false", writeDataSetBeforeImage="false"). 
 /*------------------------------------------------------------------------
    File        : bookingRestHandler
    Purpose     : 
    Syntax      : 
    Description : 
    Author(s)   : nick
    Created     : Wed Sep 10 10:52:59 UTC 2025
    Notes       : 
  ----------------------------------------------------------------------*/

USING Progress.Lang.*.
USING OpenEdge.Web.WebResponseWriter.
USING OpenEdge.Net.HTTP.StatusCodeEnum.
USING OpenEdge.Web.WebHandler.

BLOCK-LEVEL ON ERROR UNDO, THROW.

CLASS bookingRestHandler INHERITS WebHandler: 

    METHOD OVERRIDE PROTECTED INTEGER HandleNotAllowedMethod( INPUT poRequest AS OpenEdge.Web.IWebRequest ):
        
        UNDO, THROW NEW Progress.Lang.AppError("METHOD NOT IMPLEMENTED").

    END METHOD.

    METHOD OVERRIDE PROTECTED INTEGER HandleNotImplemented( INPUT poRequest AS OpenEdge.Web.IWebRequest ):
        
        UNDO, THROW NEW Progress.Lang.AppError("METHOD NOT IMPLEMENTED").

    END METHOD.

    @openapi.openedge.export(type="REST", useReturnValue="false", writeDataSetBeforeImage="false").
    METHOD PUBLIC VOID GetBooking( INPUT reg AS CHARACTER, OUTPUT BookingDate AS CHARACTER, OUTPUT Description AS CHARACTER ):
        FIND FIRST Booking WHERE Booking.Reg = reg AND Booking.BookingDate >= TODAY NO-LOCK NO-ERROR.
        IF NOT AVAILABLE Booking THEN DO:
            BookingDate = "".
            Description = "None".
        END.
        ELSE DO:
            BookingDate = STRING(DAY(Booking.BookingDate), "99") + "-" + STRING(MONTH(Booking.BookingDate), "99") + "-" + STRING(YEAR(Booking.BookingDate), "9999").
            Description = Booking.Description.
        END.
        RETURN.
    END METHOD.
    
    @openapi.openedge.export(type="REST", useReturnValue="false", writeDataSetBeforeImage="false").
    METHOD PUBLIC VOID GetNextAvailableBooking( INPUT startDate AS CHARACTER, OUTPUT bookingDate AS CHARACTER):
        DEFINE VARIABLE hBuffer AS HANDLE     NO-UNDO.
        DEFINE VARIABLE dDate   AS DATE       NO-UNDO.
        DEFINE VARIABLE bFound  AS LOGICAL    NO-UNDO.
        
        dDate = DATE(
            INTEGER(ENTRY(2, startDate, "-")),  /* month */
            INTEGER(ENTRY(1, startDate, "-")),   /* day */
            INTEGER(ENTRY(3, startDate, "-"))  /* year */
        ) + 1.
        bFound = FALSE.
        
        DO WHILE NOT bFound:
            IF WEEKDAY(dDate) >= 2 AND WEEKDAY(dDate) <= 6 AND NOT CAN-FIND(Booking WHERE Booking.BookingDate = dDate) 
            THEN bFound = TRUE. 
            ELSE dDate = dDate + 1.   
        END.
        
        bookingDate = STRING(DAY(dDate), "99") + "-" +
           STRING(MONTH(dDate), "99") + "-" +
           STRING(YEAR(dDate), "9999").
        
        RETURN.
    END METHOD.
    
    @openapi.openedge.export(type="REST", useReturnValue="false", writeDataSetBeforeImage="false").
    METHOD PUBLIC VOID SaveBooking( INPUT reg AS CHARACTER, INPUT bookingDate AS CHARACTER, INPUT description AS CHARACTER, OUTPUT response AS CHARACTER ):
        DEFINE VARIABLE dBookingDate AS DATE NO-UNDO.
        dBookingDate = DATE(
            INTEGER(ENTRY(2, bookingDate, "-")),  /* month */
            INTEGER(ENTRY(1, bookingDate, "-")),   /* day */
            INTEGER(ENTRY(3, bookingDate, "-"))  /* year */
        ).
        IF CAN-FIND(Booking WHERE Booking.BookingDate = dBookingDate) THEN DO:
            response = "A booking for the date " + STRING(dBookingDate) + " already exists".
        END.
        ELSE DO TRANSACTION:
            CREATE Booking.
            ASSIGN 
                Booking.reg = reg
                Booking.BookingDate = dBookingDate
                Booking.Description = Description.
            RELEASE Booking.
            response = "OK".
        END.
        RETURN.
    END METHOD.
       
    
END CLASS.