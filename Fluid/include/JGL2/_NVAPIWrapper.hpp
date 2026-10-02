//
//  _MathTypes.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_NVAPIWrapper_h
#define JGL2_NVAPIWrapper_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#ifdef _MSC_VER
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <NVAPI/nvapi.h>
#pragma comment( lib, "nvapi64.lib" )
#endif

namespace JGL2 {

enum class HDRMode{
	LEAVE_AS_IT_IS = 0,
	FORCE_HDR = 1,
	ASK_USER = 2,
};

#ifdef _MSC_VER
inline bool isHDREnabled( NvU32 display ) {
	NV_HDR_COLOR_DATA hdrColorData = {};

	memset(&hdrColorData, 0, sizeof(hdrColorData));

	hdrColorData.version = NV_HDR_COLOR_DATA_VER;
	hdrColorData.cmd = NV_HDR_CMD_GET;
	hdrColorData.static_metadata_descriptor_id = NV_STATIC_METADATA_TYPE_1;
	hdrColorData.static_metadata_descriptor_id = NV_STATIC_METADATA_TYPE_1;

	NvAPI_Disp_HdrColorControl( display, &hdrColorData);
	if( hdrColorData.hdrMode == NV_HDR_MODE_OFF ) return false;
	return true;
}

inline int setHDRMode( NvU32 display, bool enableHDR = true ){
	NV_HDR_COLOR_DATA hdrColorData = {};

	memset(&hdrColorData, 0, sizeof(hdrColorData));

	hdrColorData.version = NV_HDR_COLOR_DATA_VER;
	hdrColorData.cmd = NV_HDR_CMD_SET;
	hdrColorData.static_metadata_descriptor_id = NV_STATIC_METADATA_TYPE_1;
	hdrColorData.hdrMode = enableHDR ? NV_HDR_MODE_UHDA : NV_HDR_MODE_OFF;
	hdrColorData.static_metadata_descriptor_id = NV_STATIC_METADATA_TYPE_1;

	NvAPI_Disp_HdrColorControl( display, &hdrColorData);
	return true;
}
#endif

inline bool checkMonitorHDR(HDRMode mode=HDRMode::LEAVE_AS_IT_IS) {
#ifdef _MSC_VER
	bool monitorHDREnabled = false;
	if (NvAPI_Initialize() != NVAPI_OK )
	MessageBox(NULL, TEXT("NV initialization failed."), TEXT("JGL2/_NVAPIWapper"),
		MB_OK | MB_ICONINFORMATION);
	else {
		// Enumerate GPUs and connected displays
		NvPhysicalGpuHandle *nvGPUHandle = (NvPhysicalGpuHandle *)calloc(NVAPI_MAX_PHYSICAL_GPUS,
			sizeof(NvPhysicalGpuHandle));;
		NvU32 nvGPUCount;
		NvAPI_EnumPhysicalGPUs	( nvGPUHandle, &nvGPUCount );

		for( NvU32 i=0; i<nvGPUCount; i++ ) {
			NvU32 nvConnectedDisplayIdCount = 0;
			NvAPI_GPU_GetAllDisplayIds	( nvGPUHandle[i], NULL, &(nvConnectedDisplayIdCount) );
			NV_GPU_DISPLAYIDS *nvConnectedDisplayIds = (NV_GPU_DISPLAYIDS *)calloc(nvConnectedDisplayIdCount,
				sizeof(NV_GPU_DISPLAYIDS));
			for( NvU32 j=0; j<nvConnectedDisplayIdCount; j++ )
				nvConnectedDisplayIds[j].version = NV_GPU_DISPLAYIDS_VER2;
			NvAPI_GPU_GetAllDisplayIds	( nvGPUHandle[i], nvConnectedDisplayIds, &(nvConnectedDisplayIdCount) );

			for( NvU32 j=0; j<nvConnectedDisplayIdCount; j++ )
			{
				if( !nvConnectedDisplayIds[j].isActive )  continue;

				NV_HDR_CAPABILITIES hdrCapabilities = { NV_HDR_CAPABILITIES_VER2 };
				NvAPI_Status status=NvAPI_Disp_GetHdrCapabilities(nvConnectedDisplayIds[j].displayId, &hdrCapabilities);
				if (status != NVAPI_OK)
					continue;
				// If HDR is supported, break
				if( isHDREnabled(nvConnectedDisplayIds[j].displayId ) )
					monitorHDREnabled = true;
				else if (hdrCapabilities.isST2084EotfSupported ){
					int answer = IDNO;
					switch( mode ) {
						case HDRMode::FORCE_HDR:
							answer=IDYES;
							break;
						case HDRMode::ASK_USER:
							answer = MessageBox(NULL, TEXT("HDR Display found. Do you want to change to HDR mode?"),
								TEXT("JGL2/_NVAPIWapper"), MB_YESNO | MB_ICONQUESTION);
							break;
						case HDRMode::LEAVE_AS_IT_IS:
							break;
					}
					if( answer==IDYES )
						monitorHDREnabled = setHDRMode( nvConnectedDisplayIds[j].displayId, true );
				}
			}
			free(nvConnectedDisplayIds);
		}
		free(nvGPUHandle);
		NvAPI_Unload ();
	}
	return monitorHDREnabled;
#else
	return true;
#endif
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* JGL2_NVAPIWrapper_h */
