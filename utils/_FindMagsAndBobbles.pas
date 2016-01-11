{
	This needs to be in '....\FO4Edit 3.1.3\Edit Scripts' for FO4Edit to find it
	Searches all REFR records for perk mags and bobbleheads and outputs simple json to message window
	Apply Filter first to restrict to only REFR records for speed
}
unit userscript;

var eName, shortname : string;
var indexSpc : integer;

function findWorldDoor(maxdepth, cell, prevCells, targetWorld: integer,  IInterface, TStringList, integer) : IInterface;
var 
	pcell, wdoor, list, list2, listitem: IInterface;
	skipcell, i,j,k: integer;
begin
	skipcell := 0;
//	prevCells.Add(IntToStr(FixedFormID(cell)));

	list2 := ChildGroup(cell);
	for k := 0 to ElementCount(list2) -1 do begin
		list := ElementByIndex(ChildGroup(cell), k);
		for i := 0 to  ElementCount(list) - 1 do begin
			listitem := ElementByIndex(list, i);
			if ElementExists(listitem, 'XTEL') then begin
				wdoor := LinksTo(ElementByPath(listitem, 'XTEL\Door'));
				pcell := LinksTo(ElementByName(wdoor,'Cell'));

				if FixedFormID(pcell) = targetWorld then begin
					Result := wdoor;
					Exit;
				end
				else begin
					if maxdepth < 1  then begin
						Continue;
					end;
					
					for j := 0 to prevCells.Count-1 do begin
						if prevCells[j] = IntToStr(FixedFormID(pcell)) then begin
							skipcell := 1;
						end;
					end;
					if skipcell > 0 then begin
//						AddMessage('	skipping ' + IntToStr(FixedFormID(pcell) ));
					end
					else begin
						Result := findWorldDoor(maxdepth-1, pcell, prevCells, targetWorld);
						Exit;
					end;
				end;
			end;
		end;
	end;
	prevCells.Add(IntToStr(FixedFormID(cell)));

//didn't find any doors to worlds is there a marker instead?
//doesn't work, exteriors sub cell (masspikeinterchangeext4, etc) have no doors to the 
//commonwealth worldspace, and their worldx\y are correct for commonwealth anyway, and
//weird interior cells (Vault 81, Parsons State Admin, etc) still don't get
//picked up.
//			if ElementExists(cell, 'XLCN') then begin
//				wdoor := LinksTo(ElementByPath(cell, 'XLCN'));
//				if ElementExists(wdoor, 'MNAM') then begin
//					AddMessage('XLCN: ' + IntToHex(FixedFormID(wdoor),8));
//					wdoor := LinksTo(ElementByPath(wdoor, 'MNAM'));
//					AddMessage('MNAM: ' + IntToHex(FixedFormID(wdoor),8));
//					AddMessage('XMRK: ' + GetElementEditValues(wdoor, 'XMRK'));
//					AddMessage('FNAM: ' + GetElementEditValues(wdoor, 'FNAM'));
//					AddMessage('FULL: ' + GetElementEditValues(wdoor, 'FULL'));
//					AddMessage('TNAM: ' + GetElementEditValues(wdoor, 'TNAM'));
//					AddMessage('XRDS: ' + GetElementEditValues(wdoor, 'XRDS'));
//					AddMessage('EDID: ' + GetElementEditValues(wdoor, 'EDID'));
//					AddMessage('Map Marker: ' + GetElementEditValues(ElementByPath(wdoor, 'Map Marker'), 'FULL'));


//					pcell := LinksTo(ElementByName(wdoor,'Cell'));
//					if FixedFormID(pcell) = targetWorld then begin
//						Result := wdoor;
//						Exit;
//					end;
//				end;
//			end;
end;

// Called before processing
// You can remove it if script doesn't require initialization code
function Initialize: integer;
begin
	AddMessage('{"items":[');
	indexSpc := 0;
  Result := 0;
end;

// called for every record selected in xEdit
function Process(e: IInterface): integer;
	var
		RECORD_FORMID, MODEL_FILENAME: IInterface;
		sRecordFormID, sModelFilename: string;
		wdoor, pcell : IInterface;
		rec, list, listitem: IInterface;
		line, formid: string;
		i: integer;
		prevCells: TStringList;

		
begin
  Result := 0;
  if Signature(e) = 'REFR' then
  begin
	if (Pos('PerkMag', GetElementEditValues(e, 'NAME')) > 0) OR (Pos('BobbleHead_', GetElementEditValues(e, 'NAME')) > 0)  then
	begin
		if indexSpc > 0 then begin
			line := ', ';
		end 
		else begin
			line := '';
		end
		indexSpc := indexSpc + 1;
	
		eName := StringReplace(GetElementEditValues(e, 'NAME'), '"', '''',  [rfReplaceAll]);
		if (Pos('Bobble', GetElementEditValues(e, 'NAME')) > 0) then begin
			line := line + '{"type" :"bobblehead"';
		end
		else if (Pos('PerkMag', GetElementEditValues(e, 'NAME')) > 0) then begin
			line := line + '{"type" :"perkmagazine"';
		end
		
		line := line + ', "name" :"' + eName  + '"';
		line := line + ', "instanceformid" : "' + IntToHex(FixedFormID(e),8) + '"';
		line := line + ', "description" : ""';

	
		pcell := LinksTo(ElementByName(e,'Cell'));
		
		if FixedFormID(  pcell  ) = $00018AA2 then begin  //commonwealth
			line := line + ' , "world" : "' +   StringReplace(GetElementEditValues(e, 'CELL'), '"', '''',  [rfReplaceAll]) +'"';
			line := line +  ' , "worldx" : "' + GetElementEditValues(e, 'DATA\Position\X')   +'"';
			line := line +  ' , "worldy" : "' + GetElementEditValues(e, 'DATA\Position\Y')  +'"}';
			AddMessage(line);
		end
		else if FixedFormID(  pcell  ) = $00000FC5 then begin  //diamondcityfx
			line := line + ' , "world" : "' + StringReplace(GetElementEditValues(e, 'CELL'), '"', '''',  [rfReplaceAll]) +'"';
			line := line +  ' , "worldx" : "' + GetElementEditValues(e, 'DATA\Position\X')   +'"';
			line := line +  ' , "worldy" : "' + GetElementEditValues(e, 'DATA\Position\Y')  +'"}';
			AddMessage(line);
		end
		else if FixedFormID(  pcell  ) = $00000FEF then begin  //diamondcity
			line := line + ' , "world" : "' + StringReplace(GetElementEditValues(e, 'CELL'), '"', '''',  [rfReplaceAll]) +'"';
			line := line +  ' , "worldx" : "' + GetElementEditValues(e, 'DATA\Position\X')   +'"';
			line := line +  ' , "worldy" : "' + GetElementEditValues(e, 'DATA\Position\Y')  +'"}';
			AddMessage(line);
		end
		else if FixedFormID(  pcell  ) = $00054BF8 then begin  //goodneighbour
			line := line + ' , "world" : "' + StringReplace(GetElementEditValues(e, 'CELL'), '"', '''',  [rfReplaceAll]) +'"';
			line := line +  ' , "worldx" : "' + GetElementEditValues(e, 'DATA\Position\X')   +'"';
			line := line +  ' , "worldy" : "' + GetElementEditValues(e, 'DATA\Position\Y')  +'"}';
			AddMessage(line);
		end
		else if FixedFormID(  pcell  ) = $000ADF78 then begin  //sanctuaryhills
			line := line + ' , "world" : "' + StringReplace(GetElementEditValues(e, 'CELL'), '"', '''',  [rfReplaceAll]) +'"';
			line := line +  ' , "worldx" : "' + GetElementEditValues(e, 'DATA\Position\X')   +'"';
			line := line +  ' , "worldy" : "' + GetElementEditValues(e, 'DATA\Position\Y')  +'"}';
			AddMessage(line);
		end
		else begin
			line := line +  ' , "cell" : "' + StringReplace(GetElementEditValues(e, 'CELL'), '"', '''',  [rfReplaceAll])  +'"';
			line := line +  ' , "cellx" : "' + GetElementEditValues(e, 'DATA\Position\X')   +'"';
			line := line +  ' , "celly" : "' + GetElementEditValues(e, 'DATA\Position\Y')   +'"';

			prevCells := TStringList.Create;
			wdoor := findWorldDoor(50,  pcell, prevCells, $00018AA2);	//commonwealth
			shortname := GetElementEditValues(wdoor, 'DATA\Position\X');
			
			if shortname = '' then begin
				prevCells := TStringList.Create;
				wdoor := findWorldDoor(50,  pcell, prevCells, $00000FC5);  //diamondcityfx
				shortname := GetElementEditValues(wdoor, 'DATA\Position\X');
			end ;
			if shortname = '' then begin
				prevCells := TStringList.Create;
				wdoor := findWorldDoor(50,  pcell, prevCells, $00000FEF); //diamondcity
				shortname := GetElementEditValues(wdoor, 'DATA\Position\X');
			end ;
			if shortname = '' then begin
				prevCells := TStringList.Create;
				wdoor := findWorldDoor(50,  pcell, prevCells, $00054BF8); //goodneighbour
				shortname := GetElementEditValues(wdoor, 'DATA\Position\X');
			end ;
			if shortname = '' then begin
				prevCells := TStringList.Create;
				wdoor := findWorldDoor(50,  pcell, prevCells, $000ADF78); //sanctuaryhills
				shortname := GetElementEditValues(wdoor, 'DATA\Position\X');
			end ;

////			shortname := '';
////			shortname := GetElementEditValues(ElementByPath(wdoor, 'Map Marker'), 'FULL');
////			if shortname <> '' then begin  //doesn't work, is always ''
//			if ElementExists(wdoor, 'XMRK') = True then begin
//				line := line + ' , "accuracy" : "low"' ;
//			end;
			
			line := line + ' , "world" : "' + StringReplace(GetElementEditValues(wdoor, 'CELL'), '"', '''',  [rfReplaceAll]) +'"';
			line := line +  ' , "worldx" : "' + GetElementEditValues(wdoor, 'DATA\Position\X')   +'"';
			line := line +  ' , "worldy" : "' + GetElementEditValues(wdoor, 'DATA\Position\Y')  +'"}';

			AddMessage(line);
		end;
	end;
  end;
end;

// Called after processing
// You can remove it if script doesn't require finalization code
function Finalize: integer;
begin
	AddMessage(']}');
  Result := 0;
end;

end.

