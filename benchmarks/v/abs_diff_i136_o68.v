module abs_diff_i136_o68(a,b,r);
input [67:0] a,b;
output [67:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
