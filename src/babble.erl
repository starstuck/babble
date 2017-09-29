%%%-------------------------------------------------------------------
%%% @author Tomasz Szarstuk <szarsti@gmail.com>
%%% @copyright (C) 2017, Outlyer
%%% @doc
%%%
%%% Jabber echo component built based on 
%%% https://blog.process-one.net/scalable_xmpp_bots_with_erlang_and_exmpp_part_ii/
%%% @end
%%% Created : 29 Sep 2017 by Tomasz Szarstuk <szarsti@gmail.com>
%%%-------------------------------------------------------------------
-module(babble).

-behaviour(gen_server).

%% API
-export([start_link/0]).

%% gen_server callbacks
-export([init/1, handle_call/3, handle_cast/2, handle_info/2,
         terminate/2, code_change/3]).

-include_lib("xmpp/include/xmpp").

-define(SERVER, ?MODULE).
-define(COMPONENT, "metrics").
-define(SECRET, "secret").
-define(SERVER_HOST, "127.0.0.1").
-define(SERVER_PORT, 8888),


-record(state, {session}).


%%%===================================================================
%%% API
%%%===================================================================

-spec start_link() -> {ok, Pid} | ignore | {error, Error}.
start_link() ->
    gen_server:start_link({local, ?SERVER}, ?MODULE, [], []).

%%%===================================================================
%%% gen_server callbacks
%%%===================================================================

-spec init(Args) -> {ok, State}.
init([]) ->
    %%xmpp:start(),
    %%ok = web_status_db:init(),
    Session = exmpp_component:start_link(),
    exmpp_component:auth(Session, ?COMPONENT, ?SECRET),
    _StreamId = exmpp_component:connect(Session, ?SERVER_HOST, ?SERVER_PORT),
    ok = exmpp_component:handshake(Session),
   {ok, #state{session = Session}}.

-spec handle_call(Request, From, State) -> {reply, Reply, State}.
handle_call(_Request, _From, State) ->
    Reply = ok,
    {reply, Reply, State}.

-spec handle_cast(Msg, State) -> {noreply, State}.
handle_cast(_Msg, State) ->
    {noreply, State}.

-spec handle_info(Info, State) -> {noreply, State}.
handle_info(_Info, State) ->
    {noreply, State}.


handle_info(#received_packet{} = Packet, #state{session = S} = State) ->
    io:format("Received packet: %p", [Packet]),
    spawn(fun() -> process_received_packet(S, Packet) end),
    {noreply, State};

-spec terminate(Reason, State) -> void().
terminate(_Reason, _State) ->
    ok.

-spec code_change(OldVsn, State, Extra) -> {ok, NewState}.
code_change(_OldVsn, State, _Extra) ->
    {ok, State}.

%%%===================================================================
%%% Internal functions
%%%===================================================================

process_received_packet(Session,
                        #received_packet{packet_type = 'iq',
                                         type_attr = Type,
                                         raw_packet = IQ}) ->
    process_iq(Session, Type, exmpp_xml:get_ns_as_atom(exmpp_iq:get_payload(IQ)), IQ).



process_iq(Session, "get", ?NS_DISCO_INFO, IQ) ->
	Identity = exmpp_xml:element(?NS_DISCO_INFO, 'identity',
                                 [exmpp_xml:attribute("category", <<"component">>),
                                  exmpp_xml:attribute("type", <<"presence">>),
                                  exmpp_xml:attribute("name", <<"metrics">>)],
                                 []),
	IQRegisterFeature = exmpp_xml:element(?NS_DISCO_INFO, 'feature',
                                          [exmpp_xml:attribute('var', ?NS_INBAND_REGISTER_s)],
                                          []),
	Result = exmpp_iq:result(IQ, exmpp_xml:element(?NS_DISCO_INFO, 'query', [], [Identity, IQRegisterFeature])),
	exmpp_component:send_packet(Session, Result);

process_iq(Session, "get", ?NS_INBAND_REGISTER, IQ) ->
    From = exmpp_jid:parse(exmpp_stanza:get_sender(IQ)),
    %%UserConf = case web_status_db:get_user(exmpp_jid:prep_bare_to_binary(From)) of
    %%               {ok, #user{conf = Conf}} -> Conf;
    %%               not_found -> #user_conf{}
    %%           end,
    EncodedJID = base64:encode(exmpp_jid:prep_bare_to_binary(From)),
    Form = make_form(UserConf,
                     <<"Once registered, your web status URL will be: http://localhost:8080/status/",
                       EncodedJID/binary>>),
    FormInstructions = exmpp_xml:element(
                         ?NS_INBAND_REGISTER, 'instructions', [],
                         [?XMLCDATA(<<"Use the enclosed form to register">>)]),
    Result = exmpp_iq:result(IQ, 
                             exmpp_xml:element(?NS_INBAND_REGISTER, 'query', [],
                                               [FormInstructions, Form])),
    exmpp_component:send_packet(Session, Result);

process_iq(Session, "set", ?NS_INBAND_REGISTER, IQ) ->
	From = exmpp_jid:parse(exmpp_stanza:get_sender(IQ)),
	UserConf = parse_form(
                 exmpp_xml:get_element(
                   exmpp_iq:get_payload(IQ), ?NS_DATA_FORMS, 'x')),
	User = #user{bjid = exmpp_jid:prep_bare_to_binary(From),
                 conf = UserConf,
                 state = []},
	%%ok = web_status_db:store_user(User),
	exmpp_component:send_packet(Session, exmpp_iq:result(IQ)).


