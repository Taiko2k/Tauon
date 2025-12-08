// SMTC module by Taiko2k

// This needs to be compiled by Visual Studio, mingw won't work apparently.
// Put the dll in tauons /lib folder

// Interesting references
//  - https://github.com/ValleyBell/vgmplay-libvgm/blob/master/mediactrl_WinSMTC.cpp
//  - https://searchfox.org/mozilla-central/source/widget/windows/WindowsSMTCProvider.cpp


#include "pch.h"
#include <windows.h>
#include <windows.media.h>
#include <Windows.Storage.h>
#include <Windows.Storage.Streams.h>
#include <systemmediatransportcontrolsinterop.h>
#include <Windows.Foundation.h>
#include <wrl/wrappers/corewrappers.h>
#include <wrl/client.h>
#include <stdio.h>
#include <iostream>
#include <string>
#include <wrl/event.h>



using namespace ABI::Windows::Foundation;
using namespace ABI::Windows::Media;
using namespace ABI::Windows::Storage::Streams;
using namespace ABI::Windows::Storage;
using namespace Microsoft::WRL;
using namespace Microsoft::WRL::Wrappers;


typedef ITypedEventHandler<SystemMediaTransportControls*, SystemMediaTransportControlsButtonPressedEventArgs*> SMTC_ButtonPressEvt_Callback;
//typedef ITypedEventHandler<SystemMediaTransportControls*, PlaybackPositionChangeRequestedEventArgs*> PlaybacPos_ChangeReqEvt_Callback;


void (*ext_button_callback)(int);

int OnButtonPressed(ISystemMediaTransportControls*, ISystemMediaTransportControlsButtonPressedEventArgs* pArgs){
    SystemMediaTransportControlsButton btn;
    HRESULT hRes = pArgs->get_Button(&btn);

    switch (btn)
    {
        case SystemMediaTransportControlsButton_Play:
            ext_button_callback(1);
            return 0;
        case SystemMediaTransportControlsButton_Pause:
            ext_button_callback(2);
            return 0;
        case SystemMediaTransportControlsButton_Next:
            ext_button_callback(3);
            return 0;
        case SystemMediaTransportControlsButton_Previous:
            ext_button_callback(4);
            return 0;
        case SystemMediaTransportControlsButton_Stop:
            ext_button_callback(5);
            return 0;
    }

    return 1;
}

static EventRegistrationToken mBtnPressEvt;
ComPtr<SMTC_ButtonPressEvt_Callback> cbBtnPressed = Callback<SMTC_ButtonPressEvt_Callback>(OnButtonPressed);

ComPtr<ISystemMediaTransportControls> smtc;
ComPtr<ISystemMediaTransportControlsInterop> smtcInterop;
ComPtr<ISystemMediaTransportControlsDisplayUpdater> displayUpdater;
ComPtr<IMusicDisplayProperties> musicProperties;

ComPtr<IAsyncOperation<StorageFile*> > mSFileAsyncOp;


HWND windowHandle;

extern "C" {
        __declspec(dllimport) int init(void *button_callback);
        int init(void *button_callback) {

            ext_button_callback = (void (*)(int))button_callback;

            WNDCLASS wnd{};
            wnd.lpszClassName = L"Tauon-SMTC";
            wnd.hInstance = nullptr;
            wnd.lpfnWndProc = DefWindowProc;
            RegisterClass(&wnd);

            windowHandle = CreateWindowExW(0, L"Tauon-SMTC", L"Tauon Music Box Control", 0,
                CW_USEDEFAULT, CW_USEDEFAULT, 0, 0, nullptr, nullptr, nullptr, nullptr);


            HRESULT hr;

            hr = Windows::Foundation::GetActivationFactory(
                HStringReference(RuntimeClass_Windows_Media_SystemMediaTransportControls).Get(), &smtcInterop);

            if (!SUCCEEDED(hr)){
                printf("SMTC: Get activation factory failed\n");
                return 1;
            }


            hr = smtcInterop->GetForWindow(windowHandle, IID_PPV_ARGS(&smtc));

            if (!SUCCEEDED(hr)){
                DWORD lasterror = GetLastError();
                printf("SMTC: GetForWindow failed\n");
                printf("Last error reported: %lu\n", lasterror);
                return 1;
            }


            hr = smtc->get_DisplayUpdater(&displayUpdater);
            if (!SUCCEEDED(hr)){
                printf("SMTC: get DisplayUpdater failed\n");
                return 1;
            }

            smtc->put_IsEnabled(true);
            smtc->put_IsPlayEnabled(true);
            smtc->put_IsPauseEnabled(true);
            smtc->put_IsNextEnabled(true);
            smtc->put_IsPreviousEnabled(true);
            smtc->put_IsStopEnabled(true);
            smtc->put_PlaybackStatus(MediaPlaybackStatus_Stopped);
            displayUpdater->put_Type(MediaPlaybackType_Music);
            displayUpdater->Update();


            hr = displayUpdater->get_MusicProperties(&musicProperties);
            if (!SUCCEEDED(hr)) {
                printf("Error: get music properties failed!\n");
                return 1;
            }

            HSTRING hString;
            hr = WindowsCreateString(L"Tauon Music Box", 15, &hString);
            musicProperties->put_Title(hString);

            displayUpdater->Update();

            HRESULT hRes = smtc->add_ButtonPressed(cbBtnPressed.Get(), &mBtnPressEvt);

            printf("Loaded SMTC\n");
            return 0;


    }

    __declspec(dllimport) void unload();
    void unload() {
        smtc->put_IsEnabled(false);
        smtc.Reset();
        displayUpdater.Reset();
        musicProperties.Reset();
        DestroyWindow(windowHandle);
        printf("Unloaded SMTC\n");
    }

    __declspec(dllimport) void update(int state, wchar_t* title, int title_len, wchar_t* artist, int artist_len, wchar_t* thumb, int thumb_len);
    void update(int state, wchar_t* title, int title_len, wchar_t* artist, int artist_len, wchar_t* thumb, int thumb_len) {

        //wprintf(L"%s\n", thumb);  // Print thumbnail path to console

        if (state == 0) smtc->put_PlaybackStatus(MediaPlaybackStatus_Stopped);
        if (state == 1) smtc->put_PlaybackStatus(MediaPlaybackStatus_Playing);
        if (state == 2) smtc->put_PlaybackStatus(MediaPlaybackStatus_Paused);

        HSTRING hString;
        HRESULT hr;

        hr = WindowsCreateString(title, title_len + 1, &hString);
        if (!SUCCEEDED(hr)) {
            DWORD lasterror = GetLastError();
            printf("Error: creat string properties\n");
            printf("Last error reported: %lu\n", lasterror);
            return;
        }
        musicProperties->put_Title(hString);
        WindowsDeleteString(hString);

        hr = WindowsCreateString(artist, artist_len + 1, &hString);
        if (!SUCCEEDED(hr)) {
            DWORD lasterror = GetLastError();
            printf("Error: creat string properties\n");
            printf("Last error reported: %lu\n", lasterror);
            return;
        }
        musicProperties->put_Artist(hString);
        WindowsDeleteString(hString);

        // todo: There is also put_AlbumArtist to implement

        // todo: Add support for thumbnails  https://learn.microsoft.com/en-us/previous-versions/windows/desktop/mediatransport/isystemmediatransportcontrolsdisplayupdater-put-thumbnail


        displayUpdater->Update();

        return;
    }
}

