module abs_diff_i524_o262(a,b,r);
input [261:0] a,b;
output [261:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
