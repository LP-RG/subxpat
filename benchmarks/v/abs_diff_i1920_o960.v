module abs_diff_i1920_o960(a,b,r);
input [959:0] a,b;
output [959:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
