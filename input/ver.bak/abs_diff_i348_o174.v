module abs_diff_i348_o174(a,b,r);
input [173:0] a,b;
output [173:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
