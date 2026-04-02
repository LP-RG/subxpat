module abs_diff_i552_o276(a,b,r);
input [275:0] a,b;
output [275:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
