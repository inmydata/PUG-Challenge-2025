@openapi.openedge.export FILE(type="REST", executionMode="singleton", useReturnValue="false", writeDataSetBeforeImage="false").
 
 /*------------------------------------------------------------------------
    File        : carRestHandler
    Purpose     : 
    Syntax      : 
    Description : 
    Author(s)   : nick
    Created     : Mon Sep 08 12:55:40 UTC 2025
    Notes       : 
  ----------------------------------------------------------------------*/

USING Progress.Lang.*.
USING OpenEdge.Web.WebResponseWriter.
USING OpenEdge.Net.HTTP.StatusCodeEnum.
USING OpenEdge.Web.WebHandler.

BLOCK-LEVEL ON ERROR UNDO, THROW.

CLASS carRestHandler INHERITS WebHandler: 
    DEFINE TEMP-TABLE ttCar LIKE Car. 

    METHOD OVERRIDE PROTECTED INTEGER HandleNotAllowedMethod( INPUT poRequest AS OpenEdge.Web.IWebRequest ):
        
        UNDO, THROW NEW Progress.Lang.AppError("METHOD NOT IMPLEMENTED").

    END METHOD.

    METHOD OVERRIDE PROTECTED INTEGER HandleNotImplemented( INPUT poRequest AS OpenEdge.Web.IWebRequest ):
        
        UNDO, THROW NEW Progress.Lang.AppError("METHOD NOT IMPLEMENTED").

    END METHOD.

    @openapi.openedge.export(type="REST", useReturnValue="false", writeDataSetBeforeImage="false").
    METHOD PUBLIC VOID GetCar(INPUT reg AS CHARACTER, OUTPUT TABLE ttCar):
        DEFINE VARIABLE hBuffer AS HANDLE NO-UNDO.
        EMPTY TEMP-TABLE ttCar.
        FIND FIRST Car WHERE Car.reg = reg NO-LOCK NO-ERROR.
        IF AVAILABLE Car THEN DO:
            CREATE ttCar.
            BUFFER-COPY Car TO ttCar.
        END.
        RETURN.
    END.
    
    @openapi.openedge.export(type="REST", useReturnValue="false", writeDataSetBeforeImage="false").
    METHOD PUBLIC VOID SaveCar(INPUT reg AS CHARACTER, INPUT make AS CHARACTER, INPUT model AS CHARACTER, INPUT year AS INTEGER, OUTPUT response AS CHARACTER):
        IF reg="" OR reg=? THEN DO:
            response = "You must pass a valid car reg".
        END.
        ELSE DO:
            IF CAN-FIND(Car WHERE Car.reg = reg) THEN DO:
                response = "Car with reg " + reg + " already exists".
            END.
            ELSE DO TRANSACTION:
                CREATE Car.
                ASSIGN 
                    Car.reg = reg
                    Car.make = make
                    Car.model = model
                    Car.year = year.
                RELEASE Car.
                response = "OK".
            END.
        END.
        
        RETURN.
    END. 
     
       
    
END CLASS.