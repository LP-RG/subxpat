module abs_diff_i764_o382(a,b,r);
input [381:0] a,b;
output [381:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
