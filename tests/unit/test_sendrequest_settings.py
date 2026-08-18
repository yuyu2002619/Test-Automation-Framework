from unittest.mock import patch

from common.sendrequest import SendRequest
from conf import setting


def test_run_main_passes_timeout_and_tls_settings():
    requester = SendRequest()

    with patch.object(requester, 'send_request', return_value=object()) as mock_request:
        requester.run_main(
            name='配置测试',
            url='https://example.test/api',
            case_name='使用统一请求配置',
            header={'Authorization': 'Bearer fake-token'},
            method='GET',
        )

    kwargs = mock_request.call_args.kwargs
    assert kwargs['timeout'] == setting.API_TIMEOUT
    assert kwargs['verify'] is setting.TLS_VERIFY
