module abs_diff_i688_o344(a,b,r);
input [343:0] a,b;
output [343:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
