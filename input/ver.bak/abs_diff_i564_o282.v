module abs_diff_i564_o282(a,b,r);
input [281:0] a,b;
output [281:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
