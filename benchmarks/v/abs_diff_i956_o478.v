module abs_diff_i956_o478(a,b,r);
input [477:0] a,b;
output [477:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
