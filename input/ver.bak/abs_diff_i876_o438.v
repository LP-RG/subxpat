module abs_diff_i876_o438(a,b,r);
input [437:0] a,b;
output [437:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
