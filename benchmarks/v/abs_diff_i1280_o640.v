module abs_diff_i1280_o640(a,b,r);
input [639:0] a,b;
output [639:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
