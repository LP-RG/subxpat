module abs_diff_i896_o448(a,b,r);
input [447:0] a,b;
output [447:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
